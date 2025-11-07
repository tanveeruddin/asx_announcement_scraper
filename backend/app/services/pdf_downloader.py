"""
PDF Download Service

This service handles downloading PDF announcements from ASX and storing them
using the configured storage backend.

Key features:
- Downloads PDFs from ASX URLs
- Duplicate detection (skip already downloaded files)
- Retry logic with exponential backoff
- Concurrent downloads with rate limiting
- Progress tracking
"""

import logging
import hashlib
import time
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
import requests

from app.config import settings
from app.services.storage import get_storage_backend, StorageBackend
from app.services.schemas import AnnouncementData

logger = logging.getLogger(__name__)


class PDFDownloadService:
    """
    Service for downloading PDF announcements.

    This service downloads PDFs from ASX, checks for duplicates,
    and stores them using the configured storage backend.
    """

    def __init__(self, storage: Optional[StorageBackend] = None):
        """
        Initialize PDF download service.

        Args:
            storage: Storage backend to use (defaults to configured backend)
        """
        self.storage = storage or get_storage_backend()
        self.timeout = settings.request_timeout_seconds
        self.user_agent = settings.user_agent
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with proper headers."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/pdf,*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
            }
        )
        return session

    def generate_file_path(
        self, announcement: AnnouncementData, use_date_folders: bool = True
    ) -> str:
        """
        Generate storage path for a PDF file.

        Format: pdfs/YYYY/MM/ASX_CODE_YYYYMMDD_HHMMSS_HASH.pdf
        Or without date folders: pdfs/ASX_CODE_YYYYMMDD_HHMMSS_HASH.pdf

        Args:
            announcement: Announcement data
            use_date_folders: Whether to organize by year/month folders

        Returns:
            Relative file path for storage
        """
        # Extract unique identifier from PDF URL
        url_hash = hashlib.md5(announcement.pdf_url.encode()).hexdigest()[:8]

        # Format date components
        date = announcement.announcement_date
        date_str = date.strftime("%Y%m%d_%H%M%S")

        # Clean ASX code (remove special characters)
        asx_code = "".join(c for c in announcement.asx_code if c.isalnum())

        # Generate filename
        filename = f"{asx_code}_{date_str}_{url_hash}.pdf"

        # Generate path with or without date folders
        if use_date_folders:
            year = date.strftime("%Y")
            month = date.strftime("%m")
            return f"pdfs/{year}/{month}/{filename}"
        else:
            return f"pdfs/{filename}"

    def is_already_downloaded(self, file_path: str) -> bool:
        """
        Check if a PDF has already been downloaded.

        Args:
            file_path: Relative file path to check

        Returns:
            True if file exists, False otherwise
        """
        return self.storage.exists(file_path)

    def download_pdf(
        self,
        url: str,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Download a PDF from a URL with retry logic.

        Args:
            url: URL to download from
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)

        Returns:
            Tuple of (success, content, error_message)
            - success: True if download succeeded
            - content: PDF bytes if successful, None otherwise
            - error_message: Error description if failed, None if successful
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Downloading PDF from {url} (attempt {attempt + 1}/{max_retries})")

                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Verify it's actually a PDF
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and "application/octet-stream" not in content_type:
                    logger.warning(f"Unexpected content type: {content_type} for {url}")

                content = response.content

                # Basic validation: PDF files start with %PDF
                if not content.startswith(b"%PDF"):
                    error = f"Downloaded file is not a valid PDF (starts with: {content[:10]})"
                    logger.warning(error)
                    return False, None, error

                logger.debug(f"Successfully downloaded PDF ({len(content)} bytes)")
                return True, content, None

            except requests.exceptions.Timeout:
                error = f"Timeout after {self.timeout} seconds"
                logger.warning(f"{error} (attempt {attempt + 1}/{max_retries})")

            except requests.exceptions.RequestException as e:
                error = f"Request error: {e}"
                logger.warning(f"{error} (attempt {attempt + 1}/{max_retries})")

            except Exception as e:
                error = f"Unexpected error: {e}"
                logger.error(f"{error} (attempt {attempt + 1}/{max_retries})")

            # Wait before retrying (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                logger.debug(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)

        # All retries failed
        final_error = f"Failed to download after {max_retries} attempts"
        logger.error(f"{final_error}: {url}")
        return False, None, final_error

    def download_and_save(
        self,
        announcement: AnnouncementData,
        skip_if_exists: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Download and save a PDF announcement.

        Args:
            announcement: Announcement data containing PDF URL
            skip_if_exists: If True, skip download if file already exists

        Returns:
            Tuple of (success, file_path, error_message)
            - success: True if downloaded and saved (or skipped)
            - file_path: Path where file was saved, None if failed
            - error_message: Error description if failed, None if successful
        """
        try:
            # Generate file path
            file_path = self.generate_file_path(announcement)

            # Check if already downloaded
            if skip_if_exists and self.is_already_downloaded(file_path):
                logger.info(
                    f"Skipping already downloaded PDF: "
                    f"{announcement.asx_code} - {announcement.title}"
                )
                return True, file_path, None

            # Download PDF
            logger.info(
                f"Downloading PDF: {announcement.asx_code} - {announcement.title}"
            )
            success, content, error = self.download_pdf(announcement.pdf_url)

            if not success or not content:
                return False, None, error

            # Save to storage
            full_path = self.storage.save(file_path, content)

            logger.info(
                f"Successfully saved PDF: {announcement.asx_code} "
                f"({len(content)} bytes) to {file_path}"
            )

            return True, file_path, None

        except Exception as e:
            error = f"Error downloading/saving PDF: {e}"
            logger.error(error)
            return False, None, error

    def download_multiple(
        self,
        announcements: list[AnnouncementData],
        skip_if_exists: bool = True
    ) -> dict:
        """
        Download multiple PDFs (sequential, not concurrent).

        Args:
            announcements: List of announcements to download
            skip_if_exists: Skip already downloaded files

        Returns:
            Dictionary with download statistics:
            {
                'total': int,
                'successful': int,
                'skipped': int,
                'failed': int,
                'results': [{'announcement': ..., 'success': ..., 'path': ..., 'error': ...}]
            }
        """
        results = []
        stats = {
            "total": len(announcements),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
        }

        logger.info(f"Starting download of {len(announcements)} PDFs...")

        for i, announcement in enumerate(announcements, 1):
            logger.info(f"Processing {i}/{len(announcements)}: {announcement.asx_code}")

            # Check if already exists before attempting download
            file_path = self.generate_file_path(announcement)
            already_exists = self.is_already_downloaded(file_path)

            if already_exists and skip_if_exists:
                stats["skipped"] += 1
                results.append({
                    "announcement": announcement,
                    "success": True,
                    "skipped": True,
                    "path": file_path,
                    "error": None,
                })
                continue

            # Download and save
            success, path, error = self.download_and_save(
                announcement, skip_if_exists=skip_if_exists
            )

            if success:
                stats["successful"] += 1
            else:
                stats["failed"] += 1

            results.append({
                "announcement": announcement,
                "success": success,
                "skipped": False,
                "path": path,
                "error": error,
            })

            # Small delay between downloads to be respectful
            time.sleep(0.5)

        logger.info(
            f"Download complete: {stats['successful']} successful, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        stats["results"] = results
        return stats


# Create a singleton instance for easy import
pdf_downloader = PDFDownloadService()

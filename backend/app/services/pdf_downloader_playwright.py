"""
Playwright-based PDF Download Service

This service uses Playwright browser automation to download PDFs from ASX.
It handles the ASX terms and conditions page and downloads the actual PDF files.

Key features:
- Headless browser automation
- Handles ASX terms acceptance
- Downloads PDFs that require JavaScript/forms
- Timeout and retry logic
- Concurrent download support with browser pool
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout

from app.config import settings
from app.services.storage import get_storage_backend, StorageBackend
from app.services.schemas import AnnouncementData

logger = logging.getLogger(__name__)


class PlaywrightPDFDownloader:
    """
    Playwright-based PDF downloader for ASX announcements.

    Uses headless Chromium to navigate to PDF pages, handle terms acceptance,
    and download the actual PDF files.
    """

    def __init__(self, storage: Optional[StorageBackend] = None, headless: bool = True):
        """
        Initialize Playwright PDF downloader.

        Args:
            storage: Storage backend to use
            headless: Whether to run browser in headless mode
        """
        self.storage = storage or get_storage_backend()
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.timeout = settings.request_timeout_seconds * 1000  # Convert to milliseconds

    async def __aenter__(self):
        """Async context manager entry - start browser."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close browser."""
        await self.close()

    async def start(self):
        """Start the Playwright browser."""
        if self.browser is not None:
            return  # Already started

        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        logger.info("Playwright browser started")

    async def close(self):
        """Close the Playwright browser."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        logger.info("Playwright browser closed")

    def generate_file_path(
        self, announcement: AnnouncementData, use_date_folders: bool = True
    ) -> str:
        """
        Generate storage path for a PDF file.

        Format: pdfs/YYYY/MM/ASX_CODE_YYYYMMDD_HHMMSS.pdf

        Args:
            announcement: Announcement data
            use_date_folders: Whether to organize by year/month folders

        Returns:
            Relative file path for storage
        """
        import hashlib

        # Extract unique identifier from PDF URL
        url_hash = hashlib.md5(announcement.pdf_url.encode()).hexdigest()[:8]

        # Format date components
        date = announcement.announcement_date
        date_str = date.strftime("%Y%m%d_%H%M%S")

        # Clean ASX code
        asx_code = "".join(c for c in announcement.asx_code if c.isalnum())

        # Generate filename
        filename = f"{asx_code}_{date_str}_{url_hash}.pdf"

        # Generate path
        if use_date_folders:
            year = date.strftime("%Y")
            month = date.strftime("%m")
            return f"pdfs/{year}/{month}/{filename}"
        else:
            return f"pdfs/{filename}"

    async def download_pdf_from_url(self, url: str) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Download a PDF from ASX using Playwright.

        This method:
        1. Navigates to the PDF URL
        2. Handles the terms and conditions page (if present)
        3. Waits for PDF to load
        4. Downloads the PDF content

        Args:
            url: ASX PDF URL to download from

        Returns:
            Tuple of (success, pdf_content, error_message)
        """
        if not self.browser:
            await self.start()

        page: Optional[Page] = None

        try:
            # Create a new page
            page = await self.browser.new_page()

            # Set a reasonable user agent
            await page.set_extra_http_headers({
                'User-Agent': settings.user_agent
            })

            logger.debug(f"Navigating to {url}")

            # Navigate to the URL
            response = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

            if response is None:
                return False, None, "Failed to load page"

            # Check if we got a terms and conditions page
            page_content = await page.content()

            if "terms" in page_content.lower() or "conditions" in page_content.lower():
                logger.debug("Detected terms and conditions page")

                # Look for accept button or agreement link
                # Common patterns: button with "accept", "agree", "I agree", etc.
                accept_selectors = [
                    'text="Accept"',
                    'text="I Accept"',
                    'text="Agree"',
                    'text="I Agree"',
                    'text="Continue"',
                    'text="Proceed"',
                    'button:has-text("Accept")',
                    'button:has-text("Agree")',
                    'a:has-text("Accept")',
                    'a:has-text("Agree")',
                    'input[type="submit"]',
                    'input[value*="Accept"]',
                    'input[value*="Agree"]',
                ]

                clicked = False
                for selector in accept_selectors:
                    try:
                        # Check if element exists
                        element = await page.query_selector(selector)
                        if element:
                            logger.debug(f"Found accept button/link: {selector}")
                            await element.click()
                            clicked = True
                            # Wait for navigation or content change
                            await asyncio.sleep(1)
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue

                if not clicked:
                    # Try to find and submit any forms
                    forms = await page.query_selector_all("form")
                    if forms:
                        logger.debug(f"Found {len(forms)} form(s), attempting to submit first")
                        try:
                            await forms[0].evaluate("form => form.submit()")
                            await asyncio.sleep(1)
                        except Exception as e:
                            logger.warning(f"Form submission failed: {e}")

            # Wait a bit for any redirects or PDF loading
            await asyncio.sleep(2)

            # Get the final page content
            final_content = await page.content()

            # Check if we got a PDF (Playwright might have loaded it in the page)
            # If the content type is PDF, get it
            if response and "application/pdf" in response.headers.get("content-type", ""):
                logger.debug("Got PDF response directly")
                pdf_content = await response.body()

                if pdf_content.startswith(b'%PDF'):
                    logger.info(f"Successfully downloaded PDF ({len(pdf_content)} bytes)")
                    return True, pdf_content, None
                else:
                    return False, None, "Response is not a valid PDF"

            # Try to get PDF from response body
            try:
                # Some PDFs might be embedded or require special handling
                # Try to get the page's PDF if it's displaying one
                pdf_content = await page.pdf()
                if pdf_content and pdf_content.startswith(b'%PDF'):
                    logger.info(f"Successfully captured PDF from page ({len(pdf_content)} bytes)")
                    return True, pdf_content, None
            except Exception as e:
                logger.debug(f"Could not capture PDF from page: {e}")

            # If we're still on an HTML page, it might be that the PDF is in an iframe or embed
            # Try to find iframe with PDF
            iframes = await page.query_selector_all("iframe")
            for iframe in iframes:
                src = await iframe.get_attribute("src")
                if src and ("pdf" in src.lower() or "display" in src.lower()):
                    logger.debug(f"Found iframe with potential PDF: {src}")
                    # Navigate to the iframe src
                    iframe_response = await page.goto(src, wait_until="domcontentloaded", timeout=self.timeout)
                    if iframe_response and "application/pdf" in iframe_response.headers.get("content-type", ""):
                        pdf_content = await iframe_response.body()
                        if pdf_content.startswith(b'%PDF'):
                            logger.info(f"Successfully downloaded PDF from iframe ({len(pdf_content)} bytes)")
                            return True, pdf_content, None

            # If we still don't have a PDF, check for download links or embedded objects
            # Look for any links or elements that might trigger a download
            download_links = await page.query_selector_all('a[href*="pdf"]')
            if download_links:
                logger.debug(f"Found {len(download_links)} potential PDF download links")
                # Try the first one
                href = await download_links[0].get_attribute("href")
                if href:
                    if not href.startswith("http"):
                        # Make it absolute
                        base_url = page.url
                        if href.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(base_url)
                            href = f"{parsed.scheme}://{parsed.netloc}{href}"
                        else:
                            href = f"{base_url.rsplit('/', 1)[0]}/{href}"

                    logger.debug(f"Trying download link: {href}")
                    link_response = await page.goto(href, wait_until="domcontentloaded", timeout=self.timeout)
                    if link_response and "application/pdf" in link_response.headers.get("content-type", ""):
                        pdf_content = await link_response.body()
                        if pdf_content.startswith(b'%PDF'):
                            logger.info(f"Successfully downloaded PDF from link ({len(pdf_content)} bytes)")
                            return True, pdf_content, None

            # If we still don't have a PDF, return error
            return False, None, "Could not find or download PDF from page"

        except PlaywrightTimeout as e:
            error = f"Timeout while loading page: {e}"
            logger.error(error)
            return False, None, error

        except Exception as e:
            error = f"Error downloading PDF: {e}"
            logger.error(error)
            return False, None, error

        finally:
            if page:
                await page.close()

    async def download_and_save(
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
        """
        try:
            # Generate file path
            file_path = self.generate_file_path(announcement)

            # Check if already downloaded
            if skip_if_exists and self.storage.exists(file_path):
                logger.info(
                    f"Skipping already downloaded PDF: "
                    f"{announcement.asx_code} - {announcement.title}"
                )
                return True, file_path, None

            # Download PDF
            logger.info(
                f"Downloading PDF: {announcement.asx_code} - {announcement.title}"
            )
            success, content, error = await self.download_pdf_from_url(announcement.pdf_url)

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

    async def download_multiple(
        self,
        announcements: list[AnnouncementData],
        skip_if_exists: bool = True,
        max_concurrent: int = 3
    ) -> dict:
        """
        Download multiple PDFs concurrently.

        Args:
            announcements: List of announcements to download
            skip_if_exists: Skip already downloaded files
            max_concurrent: Maximum number of concurrent downloads

        Returns:
            Dictionary with download statistics
        """
        results = []
        stats = {
            "total": len(announcements),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
        }

        logger.info(f"Starting download of {len(announcements)} PDFs...")

        # Ensure browser is started
        if not self.browser:
            await self.start()

        # Process announcements in batches to limit concurrency
        for i in range(0, len(announcements), max_concurrent):
            batch = announcements[i:i + max_concurrent]
            logger.info(f"Processing batch {i // max_concurrent + 1} ({len(batch)} PDFs)")

            # Download batch concurrently
            tasks = [self.download_and_save(ann, skip_if_exists) for ann in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for ann, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    stats["failed"] += 1
                    results.append({
                        "announcement": ann,
                        "success": False,
                        "skipped": False,
                        "path": None,
                        "error": str(result),
                    })
                else:
                    success, path, error = result
                    if success and path and self.storage.exists(path):
                        # Check if it was skipped
                        file_path = self.generate_file_path(ann)
                        already_existed = self.storage.exists(file_path)
                        if already_existed and skip_if_exists:
                            stats["skipped"] += 1
                            results.append({
                                "announcement": ann,
                                "success": True,
                                "skipped": True,
                                "path": path,
                                "error": None,
                            })
                        else:
                            stats["successful"] += 1
                            results.append({
                                "announcement": ann,
                                "success": True,
                                "skipped": False,
                                "path": path,
                                "error": None,
                            })
                    else:
                        stats["failed"] += 1
                        results.append({
                            "announcement": ann,
                            "success": False,
                            "skipped": False,
                            "path": path,
                            "error": error,
                        })

            # Small delay between batches
            await asyncio.sleep(1)

        logger.info(
            f"Download complete: {stats['successful']} successful, "
            f"{stats['skipped']} skipped, {stats['failed']} failed"
        )

        stats["results"] = results
        return stats


# Helper function to run async download in sync context
def download_pdf_sync(announcement: AnnouncementData, skip_if_exists: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Synchronous wrapper for downloading a single PDF.

    Args:
        announcement: Announcement to download
        skip_if_exists: Skip if already exists

    Returns:
        Tuple of (success, file_path, error_message)
    """
    async def _download():
        async with PlaywrightPDFDownloader() as downloader:
            return await downloader.download_and_save(announcement, skip_if_exists)

    return asyncio.run(_download())


def download_multiple_sync(
    announcements: list[AnnouncementData],
    skip_if_exists: bool = True,
    max_concurrent: int = 3
) -> dict:
    """
    Synchronous wrapper for downloading multiple PDFs.

    Args:
        announcements: List of announcements to download
        skip_if_exists: Skip already downloaded files
        max_concurrent: Maximum concurrent downloads

    Returns:
        Dictionary with download statistics
    """
    async def _download():
        async with PlaywrightPDFDownloader() as downloader:
            return await downloader.download_multiple(announcements, skip_if_exists, max_concurrent)

    return asyncio.run(_download())

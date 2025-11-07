#!/usr/bin/env python3
"""
Test script for PDF downloader service.

This script tests the PDF downloader by:
1. Fetching recent announcements from ASX
2. Downloading a few PDFs
3. Verifying they're saved correctly
4. Testing duplicate detection
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from app.services.scraper import scraper_service
from app.services.pdf_downloader import pdf_downloader
from app.services.storage import get_storage_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 80 + "\n")


def main():
    """Main test function."""
    print_separator()
    print("Testing PDF Downloader Service")
    print_separator()

    # Get storage backend
    storage = get_storage_backend()
    print(f"Storage backend: {type(storage).__name__}")
    print(f"Storage location: {storage.base_path if hasattr(storage, 'base_path') else 'N/A'}")

    # Step 1: Fetch some announcements
    print_separator()
    print("Step 1: Fetching announcements from ASX...")
    result = scraper_service.scrape(price_sensitive_only=False)

    if not result.success or not result.announcements:
        print("❌ Failed to fetch announcements")
        return

    print(f"✓ Found {len(result.announcements)} announcements")

    # Step 2: Test downloading a few PDFs (first 5)
    print_separator()
    print("Step 2: Testing PDF downloads (first 5 announcements)...")

    test_announcements = result.announcements[:5]

    for i, announcement in enumerate(test_announcements, 1):
        print(f"\n{i}. Testing: [{announcement.asx_code}] {announcement.title[:60]}...")

        # Generate file path
        file_path = pdf_downloader.generate_file_path(announcement)
        print(f"   File path: {file_path}")

        # Check if already exists
        already_exists = pdf_downloader.is_already_downloaded(file_path)
        print(f"   Already exists: {already_exists}")

        # Download
        success, path, error = pdf_downloader.download_and_save(
            announcement, skip_if_exists=True
        )

        if success:
            print(f"   ✓ Success: {path}")

            # Verify file exists and get size
            if storage.exists(file_path):
                if hasattr(storage, 'get_file_size'):
                    size = storage.get_file_size(file_path)
                    print(f"   File size: {size:,} bytes")
        else:
            print(f"   ❌ Failed: {error}")

    # Step 3: Test duplicate detection
    print_separator()
    print("Step 3: Testing duplicate detection (re-download first announcement)...")

    first_announcement = test_announcements[0]
    print(f"\nRe-downloading: [{first_announcement.asx_code}] {first_announcement.title[:60]}")

    success, path, error = pdf_downloader.download_and_save(
        first_announcement, skip_if_exists=True
    )

    if success:
        print("✓ Correctly skipped already-downloaded file")
    else:
        print(f"❌ Unexpected error: {error}")

    # Step 4: Test batch download
    print_separator()
    print("Step 4: Testing batch download (10 announcements)...")

    batch_announcements = result.announcements[:10]
    stats = pdf_downloader.download_multiple(batch_announcements, skip_if_exists=True)

    print(f"\nBatch download results:")
    print(f"  Total: {stats['total']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Skipped (already exist): {stats['skipped']}")
    print(f"  Failed: {stats['failed']}")

    # Step 5: List downloaded files
    print_separator()
    print("Step 5: Listing downloaded files...")

    files = storage.list_files("pdfs/")
    print(f"\nFound {len(files)} PDF files in storage:")

    for i, file_path in enumerate(files[:20], 1):  # Show first 20
        if hasattr(storage, 'get_file_size'):
            size = storage.get_file_size(file_path)
            size_str = f"{size:,} bytes" if size else "unknown size"
        else:
            size_str = "N/A"
        print(f"  {i}. {file_path} ({size_str})")

    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more files")

    print_separator()
    print("✓ PDF Downloader test completed!")
    print_separator()


if __name__ == "__main__":
    main()

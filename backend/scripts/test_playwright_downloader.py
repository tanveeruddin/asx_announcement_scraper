#!/usr/bin/env python3
"""
Test script for Playwright PDF downloader.

This script tests the Playwright-based PDF downloader with real ASX announcements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import asyncio
from app.services.scraper import scraper_service
from app.services.pdf_downloader_playwright import PlaywrightPDFDownloader
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


async def main():
    """Main test function."""
    print_separator()
    print("Testing Playwright PDF Downloader")
    print_separator()

    # Get storage backend
    storage = get_storage_backend()
    print(f"Storage backend: {type(storage).__name__}")
    if hasattr(storage, 'base_path'):
        print(f"Storage location: {storage.base_path}")

    # Step 1: Fetch some announcements
    print_separator()
    print("Step 1: Fetching announcements from ASX...")
    result = scraper_service.scrape(price_sensitive_only=False)

    if not result.success or not result.announcements:
        print("❌ Failed to fetch announcements")
        return

    print(f"✓ Found {len(result.announcements)} announcements")

    # Step 2: Test downloading a single PDF with Playwright
    print_separator()
    print("Step 2: Testing single PDF download with Playwright...")

    test_announcement = result.announcements[0]
    print(f"\nTesting: [{test_announcement.asx_code}] {test_announcement.title[:60]}")
    print(f"PDF URL: {test_announcement.pdf_url}")

    async with PlaywrightPDFDownloader(storage=storage, headless=True) as downloader:
        success, path, error = await downloader.download_and_save(
            test_announcement, skip_if_exists=False
        )

        if success:
            print(f"✓ Success: {path}")
            if storage.exists(path):
                if hasattr(storage, 'get_file_size'):
                    size = storage.get_file_size(path)
                    print(f"  File size: {size:,} bytes")
        else:
            print(f"❌ Failed: {error}")
            return

    # Step 3: Test batch download (first 5 announcements)
    print_separator()
    print("Step 3: Testing batch download (first 5 announcements)...")

    batch_announcements = result.announcements[:5]

    async with PlaywrightPDFDownloader(storage=storage, headless=True) as downloader:
        stats = await downloader.download_multiple(
            batch_announcements,
            skip_if_exists=True,
            max_concurrent=2  # Download 2 at a time
        )

        print(f"\nBatch download results:")
        print(f"  Total: {stats['total']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Skipped (already exist): {stats['skipped']}")
        print(f"  Failed: {stats['failed']}")

        # Show details of each download
        print(f"\nDetailed results:")
        for i, r in enumerate(stats['results'], 1):
            ann = r['announcement']
            status = "✓ Skipped" if r['skipped'] else ("✓ Success" if r['success'] else "❌ Failed")
            print(f"  {i}. [{ann.asx_code}] {status}")
            if r['error']:
                print(f"     Error: {r['error']}")

    # Step 4: List downloaded files
    print_separator()
    print("Step 4: Listing downloaded PDF files...")

    files = storage.list_files("pdfs/")
    print(f"\nFound {len(files)} PDF files in storage:")

    for i, file_path in enumerate(files[:10], 1):
        if hasattr(storage, 'get_file_size'):
            size = storage.get_file_size(file_path)
            size_str = f"{size:,} bytes" if size else "unknown size"
        else:
            size_str = "N/A"
        print(f"  {i}. {file_path} ({size_str})")

    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")

    print_separator()
    print("✓ Playwright PDF Downloader test completed successfully!")
    print_separator()


if __name__ == "__main__":
    asyncio.run(main())

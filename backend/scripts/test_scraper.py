#!/usr/bin/env python3
"""
Test script for ASX scraper service.

This script tests the scraper by fetching real data from the ASX website
and displaying the results in a readable format.

Usage:
    python scripts/test_scraper.py
    or
    uv run python scripts/test_scraper.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from app.services.scraper import scraper_service

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


def display_result(result):
    """Display scraper result in a readable format."""
    print_separator()
    print("ASX SCRAPER TEST RESULTS")
    print_separator()

    print(f"Success: {result.success}")
    print(f"Scraped at: {result.scraped_at}")
    print(f"Total announcements: {result.total_count}")
    print(f"Price-sensitive: {result.price_sensitive_count}")

    if result.error_message:
        print(f"\nError: {result.error_message}")
        return

    if not result.announcements:
        print("\nNo announcements found.")
        return

    print(f"\nShowing first 10 announcements:\n")

    for i, announcement in enumerate(result.announcements[:10], 1):
        print(f"{i}. [{announcement.asx_code}] {announcement.company_name}")
        print(f"   Title: {announcement.title}")
        print(f"   Date: {announcement.announcement_date}")
        print(f"   Price-Sensitive: {announcement.is_price_sensitive}")
        print(f"   PDF: {announcement.pdf_url}")
        if announcement.num_pages:
            print(f"   Pages: {announcement.num_pages}")
        if announcement.file_size:
            print(f"   Size: {announcement.file_size}")
        print()

    if len(result.announcements) > 10:
        print(f"... and {len(result.announcements) - 10} more announcements\n")

    print_separator()


def main():
    """Main test function."""
    print_separator()
    print("Testing ASX Scraper Service")
    print("This will fetch real data from ASX website...")
    print_separator()

    # Test 1: Fetch all announcements
    print("\nTest 1: Fetching ALL announcements (price-sensitive filter OFF)")
    result = scraper_service.scrape(price_sensitive_only=False)
    display_result(result)

    # Test 2: Fetch only price-sensitive announcements
    print("\nTest 2: Fetching PRICE-SENSITIVE announcements only")
    result = scraper_service.scrape(price_sensitive_only=True)
    display_result(result)

    # Test 3: Fetch page and display raw HTML info
    print("\nTest 3: Fetching raw HTML page")
    html = scraper_service.fetch_page()
    if html:
        print(f"✓ Successfully fetched HTML page")
        print(f"  Page size: {len(html)} characters")
        print(f"  First 500 characters:\n")
        print(html[:500])
        print("\n...")
    else:
        print("✗ Failed to fetch HTML page")

    print_separator()
    print("Test completed!")
    print_separator()


if __name__ == "__main__":
    main()

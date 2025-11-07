#!/usr/bin/env python3
"""
Debug script to examine ASX HTML structure.
Saves the raw HTML to a file for inspection.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scraper import scraper_service
from bs4 import BeautifulSoup

# Fetch the page
html = scraper_service.fetch_page()

if html:
    # Save to file
    output_file = Path(__file__).parent / "asx_page.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✓ Saved HTML to: {output_file}")
    print(f"  Size: {len(html)} characters")

    # Parse and show structure
    soup = BeautifulSoup(html, "html.parser")

    print("\n=== TABLE ANALYSIS ===")
    tables = soup.find_all("table")
    print(f"Found {len(tables)} <table> elements")

    for i, table in enumerate(tables[:3], 1):  # Show first 3 tables
        print(f"\nTable {i}:")
        print(f"  Classes: {table.get('class', 'none')}")
        print(f"  ID: {table.get('id', 'none')}")
        rows = table.find_all("tr")
        print(f"  Rows: {len(rows)}")

        if rows:
            first_row = rows[0]
            cells = first_row.find_all(["td", "th"])
            print(f"  First row cells: {len(cells)}")
            if cells:
                print(f"  First row content: {[cell.get_text(strip=True)[:30] for cell in cells[:5]]}")

    print("\n=== DIV ANALYSIS ===")
    # Check for divs that might contain announcement data
    divs_with_data = soup.find_all("div", class_=lambda x: x and "announcement" in x.lower())
    print(f"Found {len(divs_with_data)} divs with 'announcement' in class name")

    # Check for common data container patterns
    for pattern in ["market-data", "data-table", "announcement", "results", "grid"]:
        matches = soup.find_all(class_=lambda x: x and pattern in x.lower())
        if matches:
            print(f"Found {len(matches)} elements with '{pattern}' in class")

    print("\n✓ Analysis complete. Check asx_page.html for full HTML")
else:
    print("✗ Failed to fetch HTML")

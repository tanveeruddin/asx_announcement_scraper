#!/usr/bin/env python3
"""Find price-sensitive announcements in the saved HTML."""

from bs4 import BeautifulSoup
from pathlib import Path

html_file = Path(__file__).parent / "asx_page.html"

with open(html_file, 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
table = soup.find('table')
rows = table.find_all('tr')[1:]  # Skip header

print(f"Total rows: {len(rows)}")

price_sensitive_found = []

for row in rows:
    cells = row.find_all('td')
    if len(cells) >= 4:
        asx_code = cells[0].get_text(strip=True)
        price_sens_cell = cells[2]
        price_sens_text = price_sens_cell.get_text(strip=True)

        if price_sens_text:  # Not empty
            price_sensitive_found.append((asx_code, price_sens_text, str(price_sens_cell)))

if price_sensitive_found:
    print(f"\nFound {len(price_sensitive_found)} price-sensitive announcements:\n")
    for asx_code, text, html in price_sensitive_found[:5]:  # Show first 5
        print(f"ASX Code: {asx_code}")
        print(f"  Text: '{text}'")
        print(f"  HTML: {html[:200]}")
        print()
else:
    print("\nNo price-sensitive announcements found today.")
    print("This might be because:")
    print("  1. Today has no price-sensitive announcements (possible)")
    print("  2. The marker is in a different format")

    # Show what the price-sens column looks like
    print("\nExample price-sens cells (first 5 rows):")
    for i, row in enumerate(rows[:5], 1):
        cells = row.find_all('td')
        if len(cells) >= 4:
            asx_code = cells[0].get_text(strip=True)
            price_sens_cell = cells[2]
            print(f"{i}. {asx_code}: '{price_sens_cell.get_text(strip=True)}' | HTML: {str(price_sens_cell)[:100]}")

#!/usr/bin/env python3
"""Debug script to examine ASX PDF URL structure."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from bs4 import BeautifulSoup

# Test URL from scraper
test_url = "https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03022343"

print(f"Testing URL: {test_url}\n")

# Fetch the URL
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

response = session.get(test_url, timeout=30)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Content-Length: {response.headers.get('content-length', 'not specified')}")
print(f"\nFirst 1000 characters of response:\n")
print(response.text[:1000])

# Check if it's HTML with embedded PDF or redirect
if 'html' in response.headers.get('content-type', '').lower():
    soup = BeautifulSoup(response.text, 'html.parser')

    # Look for PDF links or embeds
    print("\n\n=== Looking for PDF links/embeds ===\n")

    # Check for iframe
    iframes = soup.find_all('iframe')
    if iframes:
        print(f"Found {len(iframes)} iframe(s):")
        for iframe in iframes:
            print(f"  src: {iframe.get('src')}")

    # Check for embed
    embeds = soup.find_all('embed')
    if embeds:
        print(f"\nFound {len(embeds)} embed tag(s):")
        for embed in embeds:
            print(f"  src: {embed.get('src')}")

    # Check for object
    objects = soup.find_all('object')
    if objects:
        print(f"\nFound {len(objects)} object tag(s):")
        for obj in objects:
            print(f"  data: {obj.get('data')}")

    # Check for links with 'pdf' in href
    pdf_links = soup.find_all('a', href=lambda x: x and 'pdf' in x.lower())
    if pdf_links:
        print(f"\nFound {len(pdf_links)} link(s) with 'pdf':")
        for link in pdf_links[:5]:
            print(f"  href: {link.get('href')}")
            print(f"  text: {link.get_text(strip=True)[:50]}")

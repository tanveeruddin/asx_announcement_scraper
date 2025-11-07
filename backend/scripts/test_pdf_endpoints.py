#!/usr/bin/env python3
"""Test different PDF URL formats to find the working one."""

import requests

# ID from one of the announcements
doc_id = "03022343"

# Try different URL patterns
urls_to_try = [
    f"https://www.asx.com.au/asxpdf/20251107/pdf/{doc_id}.pdf",
    f"https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=file&idsId={doc_id}",
    f"https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?idsId={doc_id}",
    f"https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId={doc_id}",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.asx.com.au/asx/v2/statistics/todayAnns.do",
    "Accept": "application/pdf,text/html,application/xhtml+xml",
})

for url in urls_to_try:
    print(f"\nTrying: {url}")
    try:
        response = session.get(url, timeout=10, allow_redirects=True)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type')}")
        print(f"  Content-Length: {response.headers.get('content-length', 'N/A')}")

        # Check if it's a PDF
        if response.content.startswith(b'%PDF'):
            print(f"  ✓ SUCCESS! This is a valid PDF")
            print(f"  PDF size: {len(response.content)} bytes")
            print(f"\n✓✓✓ WORKING URL FOUND: {url}")
            break
        else:
            print(f"  ✗ Not a PDF (starts with: {response.content[:20]})")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\nDone!")

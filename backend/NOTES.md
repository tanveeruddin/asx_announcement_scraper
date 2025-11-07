# Development Notes

## PDF Download Issue (2025-11-07)

### Problem
ASX PDF links return HTML pages with terms and conditions instead of direct PDF files.

**Test URL:**
```
https://www.asx.com.au/asx/v2/statistics/displayAnnouncement.do?display=pdf&idsId=03022343
```

**Response:** HTML page with terms and conditions and a form

### Attempted Solutions

1. **Tried different URL patterns:**
   - `/asxpdf/YYYYMMDD/pdf/{id}.pdf` → 404 error
   - `display=file` parameter → HTML response
   - No display parameter → HTML response
   - Original `display=pdf` → HTML response

2. **Tried different headers:**
   - User-Agent
   - Referer header
   - Accept headers
   - None worked

### Root Cause
ASX website requires:
- Agreement to terms and conditions before PDF access
- Possibly session cookies or form submission
- May require JavaScript execution

### Potential Solutions

#### Option 1: Selenium/Playwright (Browser Automation)
Use browser automation to:
1. Load the announcement page
2. Accept terms and conditions
3. Download the PDF

**Pros:**
- Most likely to work
- Handles JavaScript and cookies
- Mimics real user behavior

**Cons:**
- Slower (browser overhead)
- Requires Chrome/Firefox driver
- More resource intensive

#### Option 2: Session Management + Form Submission
Analyze the terms form and submit it programmatically:
1. Get the form fields
2. Submit acceptance
3. Use cookies from response
4. Download PDF

**Pros:**
- Faster than browser automation
- Less resource intensive

**Cons:**
- May not work if JavaScript is required
- Form structure might change

#### Option 3: Alternative Data Source
Research if ASX provides:
- Official API for announcements
- Data feed service
- Alternative PDF hosting

**Pros:**
- More reliable
- Officially supported
- Better for production

**Cons:**
- May require paid subscription
- Might not exist

#### Option 4: Delay PDF Downloads (Recommended for MVP)
For MVP, focus on:
1. Scraping announcement metadata (working ✓)
2. Store PDF URLs for later
3. Implement PDF download in Phase 2 with proper solution

**Pros:**
- Unblocks MVP development
- Time to research proper solution
- Can implement with Selenium later

**Cons:**
- PDFs not immediately available
- Need to revisit later

### Recommended Path Forward
1. **Short term:** Store PDF URLs without downloading (MVP)
2. **Medium term:** Implement Selenium-based downloader
3. **Long term:** Contact ASX about API access or terms of service for automated access

### Action Items
- [ ] Check ASX Terms of Service regarding automated access
- [ ] Check ASX robots.txt
- [ ] Research if ASX has an official API
- [ ] Implement Selenium-based downloader if automated access is allowed
- [ ] For now: Store URLs and mark PDFs as "pending download"

### Update (Current Status)
- Scraper service: ✓ Working (275 announcements scraped)
- PDF downloader service: ✓ Implemented (code complete)
- Storage backend: ✓ Implemented (local storage working)
- **PDF downloads: ⚠️ Blocked by ASX terms page**

**Next:** Research and implement proper solution for PDF access.

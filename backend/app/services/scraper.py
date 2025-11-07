"""
ASX Announcements Scraper Service

This service scrapes the ASX announcements page to fetch today's company announcements.
It focuses on price-sensitive announcements (marked with $ symbol).

Key features:
- Fetches announcements from ASX website
- Parses HTML to extract announcement data
- Filters price-sensitive announcements
- Handles network errors and retries
- Validates and structures data using Pydantic
"""

import logging
from datetime import datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup, Tag
from app.config import settings
from app.services.schemas import AnnouncementData, ScraperResult

logger = logging.getLogger(__name__)


class ASXScraperService:
    """
    Service for scraping ASX announcements.

    The ASX website provides a daily announcements page that lists all company
    announcements in a table format. Each row contains:
    - ASX code
    - Company name
    - Announcement title
    - Date/time
    - PDF link
    - Price-sensitive indicator ($ symbol)
    """

    def __init__(self):
        self.base_url = settings.asx_url
        self.timeout = settings.request_timeout_seconds
        self.user_agent = settings.user_agent
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with proper headers."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )
        return session

    def fetch_page(self) -> Optional[str]:
        """
        Fetch the ASX announcements page HTML.

        Returns:
            HTML content as string, or None if fetch failed
        """
        try:
            logger.info(f"Fetching ASX announcements from: {self.base_url}")
            response = self.session.get(self.base_url, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Successfully fetched page (status: {response.status_code})")
            return response.text

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout} seconds")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching ASX page: {e}")
            return None

    def parse_announcements(self, html: str) -> list[AnnouncementData]:
        """
        Parse HTML and extract announcement data.

        The ASX page structure (as of 2025):
        - Announcements are in a table with class 'table-responsive' or similar
        - Each row contains: code, company, headline, date, price-sensitive marker

        Args:
            html: HTML content from ASX page

        Returns:
            List of AnnouncementData objects
        """
        soup = BeautifulSoup(html, "html.parser")
        announcements = []

        # The ASX page uses a specific table structure
        # We need to find the announcements table and parse each row
        # Note: The actual class names may need adjustment based on ASX website structure

        try:
            # Find the main announcements table
            # ASX typically uses a table or structured div layout
            rows = soup.find_all("tr")

            logger.info(f"Found {len(rows)} table rows to parse")

            for row in rows:
                try:
                    announcement = self._parse_announcement_row(row)
                    if announcement:
                        announcements.append(announcement)
                except Exception as e:
                    logger.warning(f"Failed to parse row: {e}")
                    continue

            logger.info(f"Successfully parsed {len(announcements)} announcements")

        except Exception as e:
            logger.error(f"Error parsing announcements: {e}")

        return announcements

    def _parse_announcement_row(self, row: Tag) -> Optional[AnnouncementData]:
        """
        Parse a single table row into an AnnouncementData object.

        Actual ASX page structure (as of 2025):
        Column 0: ASX Code (e.g., "BHP")
        Column 1: Date and Time (date as text, time in <span class="dates-time">)
        Column 2: Price-sensitive indicator (empty or contains $  / text)
        Column 3: Link with:
            - Announcement title (text before <br>)
            - PDF URL (in <a href>)
            - Pages (in <span class="page">)
            - File size (in <span class="filesize">)

        Args:
            row: BeautifulSoup Tag representing a table row

        Returns:
            AnnouncementData object or None if parsing fails
        """
        try:
            cells = row.find_all("td")

            # Skip header rows or invalid rows (need exactly 4 columns)
            if len(cells) != 4:
                return None

            # Column 0: ASX Code
            asx_code = cells[0].get_text(strip=True)
            if not asx_code or len(asx_code) > 10:  # Sanity check
                return None

            # Column 1: Date and Time
            date_cell = cells[1]
            date_parts = date_cell.get_text(strip=False).strip().split('\n')
            date_str = date_parts[0].strip() if date_parts else ""

            # Extract time from span
            time_span = date_cell.find("span", class_="dates-time")
            time_str = time_span.get_text(strip=True) if time_span else ""

            full_date_str = f"{date_str} {time_str}".strip()
            if not full_date_str:
                logger.debug(f"No date found for {asx_code}")
                return None

            # Column 2: Price-sensitive indicator
            price_sens_cell = cells[2]
            is_price_sensitive = self._is_price_sensitive(price_sens_cell)

            # Column 3: Announcement details
            details_cell = cells[3]
            link = details_cell.find("a", href=True)
            if not link:
                logger.debug(f"No link found for {asx_code}")
                return None

            # Extract PDF URL
            pdf_url = self._extract_pdf_url(link)
            if not pdf_url:
                logger.debug(f"No PDF URL found for {asx_code}")
                return None

            # Extract title (text before <br> tag, or first text node)
            title = self._extract_title(link)
            if not title:
                logger.debug(f"No title found for {asx_code}")
                return None

            # Parse announcement date
            announcement_date = self._parse_date(full_date_str)

            # Extract additional metadata
            num_pages = self._extract_num_pages(details_cell)
            file_size = self._extract_file_size(details_cell)

            # Note: ASX doesn't provide company name in the table
            # We'll use ASX code as company name for now, or look it up later
            company_name = asx_code  # Will be enriched later

            return AnnouncementData(
                asx_code=asx_code,
                company_name=company_name,
                title=title,
                announcement_date=announcement_date,
                pdf_url=pdf_url,
                is_price_sensitive=is_price_sensitive,
                num_pages=num_pages,
                file_size=file_size,
            )

        except Exception as e:
            logger.debug(f"Error parsing row: {e}")
            return None

    def _is_price_sensitive(self, price_sens_cell: Tag) -> bool:
        """
        Determine if announcement is price-sensitive.

        ASX marks price-sensitive announcements with content in the 3rd column:
        - A $ symbol
        - Text like "Yes" or "Price Sensitive"
        - Or other indicator

        Args:
            price_sens_cell: The price-sensitive table cell (column 2)

        Returns:
            True if price-sensitive, False otherwise
        """
        cell_text = price_sens_cell.get_text(strip=True)

        # If cell has any non-whitespace content, it's price-sensitive
        if cell_text:
            return True

        # Check for images or other indicators
        if price_sens_cell.find("img"):
            return True

        # Check for $ symbol or specific class
        if "$" in str(price_sens_cell):
            return True

        return False

    def _extract_pdf_url(self, link: Tag) -> Optional[str]:
        """
        Extract PDF download URL from anchor tag.

        Args:
            link: The anchor tag containing the PDF link

        Returns:
            Full PDF URL or None if not found
        """
        if not link or not link.get("href"):
            return None

        href = link["href"]

        # Handle relative URLs
        if href.startswith("/"):
            return f"https://www.asx.com.au{href}"
        elif href.startswith("http"):
            return href

        return None

    def _extract_title(self, link: Tag) -> Optional[str]:
        """
        Extract announcement title from link.

        The title is the text content before the first <br> tag.

        Args:
            link: The anchor tag containing the announcement

        Returns:
            Title string or None if not found
        """
        # Get all text nodes before <br>
        title_parts = []
        for content in link.contents:
            if content.name == "br":
                break
            if isinstance(content, str):
                title_parts.append(content.strip())

        title = " ".join(title_parts).strip()
        return title if title else None

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string from ASX format.

        ASX typically uses format like: "07/11/2025  09:30 AM"
        or "07/11/2025  9:30:00 AM"

        Args:
            date_str: Date string from ASX

        Returns:
            Parsed datetime object
        """
        # Clean up the string
        date_str = date_str.strip()

        # Try common ASX date formats
        formats = [
            "%d/%m/%Y  %I:%M %p",      # 07/11/2025  09:30 AM
            "%d/%m/%Y  %I:%M:%S %p",   # 07/11/2025  9:30:00 AM
            "%d/%m/%Y %I:%M %p",       # 07/11/2025 09:30 AM
            "%d/%m/%Y %H:%M:%S",       # 07/11/2025 09:30:00
            "%d/%m/%Y %H:%M",          # 07/11/2025 09:30
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # If all formats fail, log warning and return current time
        logger.warning(f"Could not parse date: {date_str}, using current time")
        return datetime.now()

    def _extract_num_pages(self, details_cell: Tag) -> Optional[int]:
        """
        Extract number of pages from details cell.

        Args:
            details_cell: The cell containing announcement details

        Returns:
            Number of pages or None if not found
        """
        page_span = details_cell.find("span", class_="page")
        if page_span:
            text = page_span.get_text()
            # Extract number (e.g., "7 pages" -> 7, "1 page" -> 1)
            import re
            match = re.search(r"(\d+)", text)
            if match:
                return int(match.group(1))
        return None

    def _extract_file_size(self, details_cell: Tag) -> Optional[str]:
        """
        Extract file size from details cell.

        Args:
            details_cell: The cell containing announcement details

        Returns:
            File size string (e.g., "58.5KB") or None if not found
        """
        filesize_span = details_cell.find("span", class_="filesize")
        if filesize_span:
            return filesize_span.get_text(strip=True)
        return None

    def filter_price_sensitive(
        self, announcements: list[AnnouncementData]
    ) -> list[AnnouncementData]:
        """
        Filter announcements to only include price-sensitive ones.

        Args:
            announcements: List of all announcements

        Returns:
            Filtered list containing only price-sensitive announcements
        """
        price_sensitive = [a for a in announcements if a.is_price_sensitive]
        logger.info(
            f"Filtered to {len(price_sensitive)} price-sensitive "
            f"announcements from {len(announcements)} total"
        )
        return price_sensitive

    def scrape(self, price_sensitive_only: bool = True) -> ScraperResult:
        """
        Main method to scrape ASX announcements.

        Args:
            price_sensitive_only: If True, only return price-sensitive announcements

        Returns:
            ScraperResult with announcements and metadata
        """
        try:
            # Fetch the page
            html = self.fetch_page()
            if not html:
                return ScraperResult(
                    announcements=[],
                    total_count=0,
                    price_sensitive_count=0,
                    success=False,
                    error_message="Failed to fetch ASX page",
                )

            # Parse announcements
            announcements = self.parse_announcements(html)

            # Count price-sensitive before filtering
            price_sensitive_count = sum(1 for a in announcements if a.is_price_sensitive)

            # Filter if requested
            if price_sensitive_only:
                announcements = self.filter_price_sensitive(announcements)

            logger.info(
                f"Scrape completed: {len(announcements)} announcements "
                f"({price_sensitive_count} price-sensitive)"
            )

            return ScraperResult(
                announcements=announcements,
                total_count=len(announcements),
                price_sensitive_count=price_sensitive_count,
                success=True,
            )

        except Exception as e:
            logger.error(f"Error during scraping: {e}", exc_info=True)
            return ScraperResult(
                announcements=[],
                total_count=0,
                price_sensitive_count=0,
                success=False,
                error_message=str(e),
            )


# Create a singleton instance for easy import
scraper_service = ASXScraperService()

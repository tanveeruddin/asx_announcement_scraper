"""
Pydantic schemas for service layer data transfer objects.
These schemas are used for data validation and serialization between services.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class AnnouncementData(BaseModel):
    """
    Data structure for a raw announcement scraped from ASX.
    This is the output format from the scraper service.
    """

    asx_code: str = Field(..., description="ASX stock code (e.g., 'BHP', 'CBA')")
    company_name: str = Field(..., description="Full company name")
    title: str = Field(..., description="Announcement title/headline")
    announcement_date: datetime = Field(..., description="Date and time of announcement")
    pdf_url: str = Field(..., description="URL to download the PDF announcement")
    is_price_sensitive: bool = Field(
        default=False, description="Whether announcement is marked as price-sensitive"
    )
    num_pages: Optional[int] = Field(default=None, description="Number of pages in PDF")
    file_size: Optional[str] = Field(default=None, description="File size (e.g., '250K')")

    class Config:
        json_schema_extra = {
            "example": {
                "asx_code": "BHP",
                "company_name": "BHP Group Limited",
                "title": "Quarterly Production Report",
                "announcement_date": "2025-11-07T09:30:00",
                "pdf_url": "https://www.asx.com.au/asxpdf/20251107/pdf/123456.pdf",
                "is_price_sensitive": True,
                "num_pages": 15,
                "file_size": "250K",
            }
        }


class ScraperResult(BaseModel):
    """
    Result of a scraping operation.
    Contains all announcements found and metadata about the scrape.
    """

    announcements: list[AnnouncementData] = Field(
        default_factory=list, description="List of announcements found"
    )
    total_count: int = Field(..., description="Total number of announcements scraped")
    price_sensitive_count: int = Field(
        ..., description="Number of price-sensitive announcements"
    )
    scraped_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the scrape was performed"
    )
    success: bool = Field(default=True, description="Whether scrape was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if scrape failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "announcements": [],
                "total_count": 150,
                "price_sensitive_count": 45,
                "scraped_at": "2025-11-07T10:30:00",
                "success": True,
                "error_message": None,
            }
        }

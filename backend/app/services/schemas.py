"""
Pydantic schemas for service layer data transfer objects.
These schemas are used for data validation and serialization between services.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
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


class AnalysisResult(BaseModel):
    """
    Result of LLM analysis for an announcement.
    Contains extracted summary, sentiment, and key insights.
    """

    summary: str = Field(..., description="2-3 sentence summary of the announcement")
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        ..., description="Market sentiment classification"
    )
    key_insights: list[str] = Field(
        default_factory=list,
        description="3-5 most important takeaways from the announcement",
    )
    financial_impact: Optional[str] = Field(
        default=None, description="Estimated potential impact on stock price"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score of the analysis (0-1)"
    )
    llm_model: str = Field(..., description="LLM model used for analysis")
    processing_time_ms: Optional[int] = Field(
        default=None, description="Time taken to process in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "BHP Group reported strong quarterly production figures with iron ore output exceeding market expectations by 5%.",
                "sentiment": "bullish",
                "key_insights": [
                    "Iron ore production up 5% vs expectations",
                    "Copper production stable despite weather challenges",
                    "Cost reduction initiatives on track",
                ],
                "financial_impact": "Positive - likely to support share price in short term",
                "confidence_score": 0.85,
                "llm_model": "gemini-1.5-pro",
                "processing_time_ms": 1250,
            }
        }


class StockMetrics(BaseModel):
    """
    Stock market data and performance metrics for a company.
    Fetched from yfinance at the time of announcement.
    """

    asx_code: str = Field(..., description="ASX stock code")
    current_price: Optional[Decimal] = Field(
        default=None, description="Current stock price in AUD"
    )
    price_at_announcement: Optional[Decimal] = Field(
        default=None, description="Stock price at announcement time"
    )
    market_cap: Optional[Decimal] = Field(
        default=None, description="Market capitalization in AUD"
    )
    pe_ratio: Optional[Decimal] = Field(
        default=None, description="Price-to-earnings ratio"
    )
    volume: Optional[int] = Field(
        default=None, description="Trading volume"
    )
    performance_1m_pct: Optional[Decimal] = Field(
        default=None, description="1-month price performance percentage"
    )
    performance_3m_pct: Optional[Decimal] = Field(
        default=None, description="3-month price performance percentage"
    )
    performance_6m_pct: Optional[Decimal] = Field(
        default=None, description="6-month price performance percentage"
    )
    price_change_1h_pct: Optional[Decimal] = Field(
        default=None, description="Price change 1 hour after announcement (%)"
    )
    price_change_1d_pct: Optional[Decimal] = Field(
        default=None, description="Price change 1 day after announcement (%)"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the data was fetched"
    )
    data_available: bool = Field(
        default=True, description="Whether stock data was successfully fetched"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if data fetch failed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "asx_code": "BHP",
                "current_price": "45.23",
                "price_at_announcement": "44.85",
                "market_cap": "228500000000",
                "pe_ratio": "12.5",
                "volume": 15420000,
                "performance_1m_pct": "3.2",
                "performance_3m_pct": "8.7",
                "performance_6m_pct": "15.3",
                "price_change_1h_pct": "0.85",
                "price_change_1d_pct": "1.2",
                "fetched_at": "2025-11-07T10:30:00",
                "data_available": True,
                "error_message": None,
            }
        }

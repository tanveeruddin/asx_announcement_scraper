"""
Pydantic schemas for API requests and responses.

These schemas define the structure of data exchanged between the API and clients,
providing validation, serialization, and documentation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# Base schemas

class CompanyBase(BaseModel):
    """Base company schema."""
    asx_code: str = Field(..., description="ASX stock code (e.g., 'BHP', 'CBA')")
    company_name: str = Field(..., description="Full company name")
    industry: Optional[str] = Field(None, description="Industry sector")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization in AUD")


class CompanyResponse(CompanyBase):
    """Company response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    last_updated: datetime
    created_at: datetime


class AnalysisResponse(BaseModel):
    """Analysis response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    announcement_id: UUID
    summary: Optional[str] = None
    sentiment: Optional[Literal["bullish", "bearish", "neutral"]] = None
    key_insights: Optional[List[str]] = None
    llm_model: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime


class StockDataResponse(BaseModel):
    """Stock data response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    announcement_id: UUID
    company_id: UUID
    price_at_announcement: Optional[Decimal] = None
    price_1h_after: Optional[Decimal] = None
    price_1d_after: Optional[Decimal] = None
    price_change_pct: Optional[Decimal] = None
    volume_at_announcement: Optional[int] = None
    market_cap: Optional[Decimal] = None
    pe_ratio: Optional[Decimal] = None
    performance_1m_pct: Optional[Decimal] = None
    performance_3m_pct: Optional[Decimal] = None
    performance_6m_pct: Optional[Decimal] = None
    fetched_at: datetime


class AnnouncementBase(BaseModel):
    """Base announcement schema."""
    asx_code: str = Field(..., description="ASX stock code")
    title: str = Field(..., description="Announcement title/headline")
    announcement_date: datetime = Field(..., description="Date and time of announcement")
    pdf_url: str = Field(..., description="URL to PDF document")
    is_price_sensitive: bool = Field(default=False, description="Price-sensitive flag")
    num_pages: Optional[int] = Field(None, description="Number of pages in PDF")
    file_size_kb: Optional[int] = Field(None, description="File size in kilobytes")


class AnnouncementListResponse(AnnouncementBase):
    """Announcement response for list views (without full details)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    company: Optional[CompanyResponse] = None
    downloaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    # Include basic analysis info if available
    sentiment: Optional[str] = None  # From analysis relationship


class AnnouncementDetailResponse(AnnouncementListResponse):
    """Announcement response with full details (includes analysis and stock data)."""
    pdf_local_path: Optional[str] = None
    markdown_path: Optional[str] = None

    # Related data
    analysis: Optional[AnalysisResponse] = None
    stock_data: Optional[List[StockDataResponse]] = None


class AnnouncementCreateRequest(AnnouncementBase):
    """Request schema for creating an announcement."""
    company_id: UUID


# Pagination

class PaginationMetadata(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")


class PaginatedAnnouncementsResponse(BaseModel):
    """Paginated announcements response."""
    items: List[AnnouncementListResponse] = Field(..., description="List of announcements")
    metadata: PaginationMetadata = Field(..., description="Pagination metadata")


# Search

class AnnouncementSearchRequest(BaseModel):
    """Advanced search request for announcements."""
    query: Optional[str] = Field(None, description="Text search query (searches title)")
    asx_codes: Optional[List[str]] = Field(None, description="List of ASX codes to filter by")
    date_from: Optional[datetime] = Field(None, description="Filter from this date")
    date_to: Optional[datetime] = Field(None, description="Filter until this date")
    price_sensitive_only: bool = Field(default=False, description="Only price-sensitive announcements")
    sentiment: Optional[Literal["bullish", "bearish", "neutral"]] = Field(
        None, description="Filter by sentiment"
    )
    min_market_cap: Optional[Decimal] = Field(None, description="Minimum market cap (AUD)")
    max_market_cap: Optional[Decimal] = Field(None, description="Maximum market cap (AUD)")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Literal["date", "asx_code", "market_cap"] = Field(
        default="date", description="Sort field"
    )
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort order")


# Statistics

class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    total_announcements: int
    price_sensitive_count: int
    announcements_today: int
    announcements_this_week: int
    announcements_this_month: int
    unique_companies: int
    sentiment_breakdown: dict[str, int]  # {bullish: X, bearish: Y, neutral: Z}
    top_companies: List[dict]  # [{asx_code, company_name, count}, ...]


# Health Check

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    version: str
    database: Literal["connected", "disconnected"]
    scraper: Optional[dict] = None  # Last scrape info


# Error Response

class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

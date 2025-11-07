"""
API routes for announcements.

Provides endpoints for fetching, searching, and filtering ASX announcements.
"""

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    AnnouncementDetailResponse,
    AnnouncementListResponse,
    AnnouncementSearchRequest,
    PaginatedAnnouncementsResponse,
    PaginationMetadata,
)
from app.db.crud import AnnouncementService
from app.db.session import get_db

router = APIRouter(prefix="/announcements", tags=["announcements"])


@router.get("", response_model=PaginatedAnnouncementsResponse)
async def get_announcements(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    asx_code: Optional[str] = Query(None, description="Filter by ASX code"),
    price_sensitive_only: bool = Query(False, description="Only price-sensitive announcements"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment (bullish/bearish/neutral)"),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of announcements with optional filters.

    **Filters:**
    - `asx_code`: Filter by specific ASX stock code
    - `price_sensitive_only`: Show only price-sensitive announcements
    - `date_from` / `date_to`: Date range filter
    - `sentiment`: Filter by LLM-analyzed sentiment

    **Pagination:**
    - `page`: Page number (starts at 1)
    - `page_size`: Number of items per page (max 100)

    **Returns:**
    - Paginated list of announcements with metadata
    """
    # Calculate skip offset
    skip = (page - 1) * page_size

    # Get announcements
    announcements = AnnouncementService.get_multi(
        db=db,
        skip=skip,
        limit=page_size,
        asx_code=asx_code,
        price_sensitive_only=price_sensitive_only,
        date_from=date_from,
        date_to=date_to,
        sentiment=sentiment,
    )

    # Get total count for pagination
    total = AnnouncementService.count(
        db=db,
        asx_code=asx_code,
        price_sensitive_only=price_sensitive_only,
        date_from=date_from,
        date_to=date_to,
    )

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    # Convert to response models
    items = []
    for announcement in announcements:
        # Get sentiment from analysis if available
        sentiment_value = None
        if announcement.analysis:
            sentiment_value = announcement.analysis.sentiment

        # Create response
        item = AnnouncementListResponse.model_validate(announcement)
        item.sentiment = sentiment_value
        items.append(item)

    # Build response
    return PaginatedAnnouncementsResponse(
        items=items,
        metadata=PaginationMetadata(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )


@router.get("/{announcement_id}", response_model=AnnouncementDetailResponse)
async def get_announcement(
    announcement_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific announcement.

    **Includes:**
    - Full announcement details
    - Company information
    - LLM analysis (summary, sentiment, insights)
    - Stock data and market metrics

    **Args:**
    - `announcement_id`: UUID of the announcement

    **Returns:**
    - Complete announcement details with all related data

    **Raises:**
    - `404`: Announcement not found
    """
    announcement = AnnouncementService.get_by_id(db, announcement_id)

    if not announcement:
        raise HTTPException(
            status_code=404,
            detail=f"Announcement with ID {announcement_id} not found",
        )

    return AnnouncementDetailResponse.model_validate(announcement)


@router.post("/search", response_model=PaginatedAnnouncementsResponse)
async def search_announcements(
    search_request: AnnouncementSearchRequest,
    db: Session = Depends(get_db),
):
    """
    Advanced search for announcements with multiple filters.

    **Search Capabilities:**
    - Text search in announcement titles
    - Multiple ASX codes
    - Date range
    - Price sensitivity filter
    - Sentiment filter (from LLM analysis)
    - Market cap range
    - Custom sorting

    **Example Request:**
    ```json
    {
      "query": "quarterly",
      "asx_codes": ["BHP", "RIO", "FMG"],
      "date_from": "2025-01-01T00:00:00",
      "price_sensitive_only": true,
      "sentiment": "bullish",
      "min_market_cap": 1000000000,
      "page": 1,
      "page_size": 20,
      "sort_by": "date",
      "sort_order": "desc"
    }
    ```

    **Returns:**
    - Paginated search results
    """
    # TODO: Implement full-text search and advanced filtering
    # For now, use basic filtering from get_multi

    # Calculate skip offset
    skip = (search_request.page - 1) * search_request.page_size

    # Build filters (basic implementation)
    asx_code = None
    if search_request.asx_codes and len(search_request.asx_codes) == 1:
        asx_code = search_request.asx_codes[0]

    # Get announcements
    announcements = AnnouncementService.get_multi(
        db=db,
        skip=skip,
        limit=search_request.page_size,
        asx_code=asx_code,
        price_sensitive_only=search_request.price_sensitive_only,
        date_from=search_request.date_from,
        date_to=search_request.date_to,
        sentiment=search_request.sentiment,
    )

    # Get total count
    total = AnnouncementService.count(
        db=db,
        asx_code=asx_code,
        price_sensitive_only=search_request.price_sensitive_only,
        date_from=search_request.date_from,
        date_to=search_request.date_to,
    )

    # Calculate total pages
    total_pages = math.ceil(total / search_request.page_size) if total > 0 else 1

    # Convert to response models
    items = []
    for announcement in announcements:
        sentiment_value = None
        if announcement.analysis:
            sentiment_value = announcement.analysis.sentiment

        item = AnnouncementListResponse.model_validate(announcement)
        item.sentiment = sentiment_value
        items.append(item)

    return PaginatedAnnouncementsResponse(
        items=items,
        metadata=PaginationMetadata(
            total=total,
            page=search_request.page,
            page_size=search_request.page_size,
            total_pages=total_pages,
        ),
    )

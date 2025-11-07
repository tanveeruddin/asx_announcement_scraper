"""
API routes for companies.

Provides endpoints for fetching company information and their announcements.
"""

import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.schemas import (
    CompanyResponse,
    PaginatedAnnouncementsResponse,
    AnnouncementListResponse,
    PaginationMetadata,
)
from app.db.crud import CompanyService, AnnouncementService
from app.db.session import get_db

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyResponse])
async def get_companies(
    skip: int = Query(0, ge=0, description="Number of companies to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max companies to return"),
    db: Session = Depends(get_db),
):
    """
    Get list of all ASX companies.

    **Pagination:**
    - `skip`: Number of companies to skip
    - `limit`: Maximum companies to return (max 500)

    **Returns:**
    - List of companies with basic information
    """
    companies = CompanyService.get_multi(db=db, skip=skip, limit=limit)
    return [CompanyResponse.model_validate(company) for company in companies]


@router.get("/{asx_code}", response_model=CompanyResponse)
async def get_company(
    asx_code: str,
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific company.

    **Args:**
    - `asx_code`: ASX stock code (e.g., 'BHP', 'CBA')

    **Returns:**
    - Company details including market cap and industry

    **Raises:**
    - `404`: Company not found
    """
    company = CompanyService.get_by_asx_code(db, asx_code)

    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company with ASX code '{asx_code}' not found",
        )

    return CompanyResponse.model_validate(company)


@router.get("/{asx_code}/announcements", response_model=PaginatedAnnouncementsResponse)
async def get_company_announcements(
    asx_code: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    price_sensitive_only: bool = Query(False, description="Only price-sensitive announcements"),
    db: Session = Depends(get_db),
):
    """
    Get all announcements for a specific company.

    **Args:**
    - `asx_code`: ASX stock code

    **Filters:**
    - `price_sensitive_only`: Show only price-sensitive announcements

    **Pagination:**
    - `page`: Page number (starts at 1)
    - `page_size`: Number of items per page (max 100)

    **Returns:**
    - Paginated list of company announcements

    **Raises:**
    - `404`: Company not found
    """
    # Check if company exists
    company = CompanyService.get_by_asx_code(db, asx_code)
    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company with ASX code '{asx_code}' not found",
        )

    # Calculate skip offset
    skip = (page - 1) * page_size

    # Get announcements for this company
    announcements = AnnouncementService.get_multi(
        db=db,
        skip=skip,
        limit=page_size,
        asx_code=asx_code,
        price_sensitive_only=price_sensitive_only,
    )

    # Get total count
    total = AnnouncementService.count(
        db=db,
        asx_code=asx_code,
        price_sensitive_only=price_sensitive_only,
    )

    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 1

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
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    )

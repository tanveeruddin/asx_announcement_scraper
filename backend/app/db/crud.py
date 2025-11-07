"""
Database service layer for CRUD operations.

This module provides high-level database operations for all models,
abstracting SQLAlchemy queries and providing a clean interface for the API layer.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models.announcement import Announcement
from app.models.analysis import Analysis
from app.models.company import Company
from app.models.stock_data import StockData


class AnnouncementService:
    """Service for announcement database operations."""

    @staticmethod
    def create(db: Session, announcement_data: dict) -> Announcement:
        """
        Create a new announcement.

        Args:
            db: Database session
            announcement_data: Dictionary containing announcement data

        Returns:
            Created Announcement instance
        """
        announcement = Announcement(**announcement_data)
        db.add(announcement)
        db.commit()
        db.refresh(announcement)
        return announcement

    @staticmethod
    def get_by_id(db: Session, announcement_id: UUID) -> Optional[Announcement]:
        """
        Get announcement by ID with related data.

        Args:
            db: Database session
            announcement_id: Announcement UUID

        Returns:
            Announcement instance or None
        """
        return (
            db.query(Announcement)
            .options(
                joinedload(Announcement.company),
                joinedload(Announcement.analysis),
                joinedload(Announcement.stock_data),
            )
            .filter(Announcement.id == announcement_id)
            .first()
        )

    @staticmethod
    def get_multi(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        asx_code: Optional[str] = None,
        price_sensitive_only: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
    ) -> List[Announcement]:
        """
        Get multiple announcements with filters and pagination.

        Args:
            db: Database session
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            asx_code: Filter by ASX code
            price_sensitive_only: If True, only return price-sensitive announcements
            date_from: Filter announcements from this date
            date_to: Filter announcements until this date
            sentiment: Filter by sentiment (from analysis)

        Returns:
            List of Announcement instances
        """
        query = db.query(Announcement).options(
            joinedload(Announcement.company),
            joinedload(Announcement.analysis),
        )

        # Apply filters
        if asx_code:
            query = query.filter(Announcement.asx_code == asx_code.upper())

        if price_sensitive_only:
            query = query.filter(Announcement.is_price_sensitive == True)

        if date_from:
            query = query.filter(Announcement.announcement_date >= date_from)

        if date_to:
            query = query.filter(Announcement.announcement_date <= date_to)

        if sentiment:
            query = query.join(Analysis).filter(Analysis.sentiment == sentiment.lower())

        # Order by announcement date (newest first)
        query = query.order_by(desc(Announcement.announcement_date))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def count(
        db: Session,
        asx_code: Optional[str] = None,
        price_sensitive_only: bool = False,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """
        Count announcements with filters.

        Args:
            db: Database session
            asx_code: Filter by ASX code
            price_sensitive_only: If True, only count price-sensitive announcements
            date_from: Filter announcements from this date
            date_to: Filter announcements until this date

        Returns:
            Count of matching announcements
        """
        query = db.query(Announcement)

        if asx_code:
            query = query.filter(Announcement.asx_code == asx_code.upper())

        if price_sensitive_only:
            query = query.filter(Announcement.is_price_sensitive == True)

        if date_from:
            query = query.filter(Announcement.announcement_date >= date_from)

        if date_to:
            query = query.filter(Announcement.announcement_date <= date_to)

        return query.count()

    @staticmethod
    def update(
        db: Session, announcement_id: UUID, update_data: dict
    ) -> Optional[Announcement]:
        """
        Update an announcement.

        Args:
            db: Database session
            announcement_id: Announcement UUID
            update_data: Dictionary of fields to update

        Returns:
            Updated Announcement or None if not found
        """
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if announcement:
            for key, value in update_data.items():
                setattr(announcement, key, value)
            db.commit()
            db.refresh(announcement)
        return announcement

    @staticmethod
    def delete(db: Session, announcement_id: UUID) -> bool:
        """
        Delete an announcement.

        Args:
            db: Database session
            announcement_id: Announcement UUID

        Returns:
            True if deleted, False if not found
        """
        announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if announcement:
            db.delete(announcement)
            db.commit()
            return True
        return False

    @staticmethod
    def exists(
        db: Session,
        asx_code: str,
        announcement_date: datetime,
        title: str,
    ) -> bool:
        """
        Check if announcement already exists (for duplicate detection).

        Args:
            db: Database session
            asx_code: ASX code
            announcement_date: Announcement date
            title: Announcement title

        Returns:
            True if exists, False otherwise
        """
        return (
            db.query(Announcement)
            .filter(
                and_(
                    Announcement.asx_code == asx_code.upper(),
                    Announcement.announcement_date == announcement_date,
                    Announcement.title == title,
                )
            )
            .first()
            is not None
        )


class CompanyService:
    """Service for company database operations."""

    @staticmethod
    def create(db: Session, company_data: dict) -> Company:
        """Create a new company."""
        company = Company(**company_data)
        db.add(company)
        db.commit()
        db.refresh(company)
        return company

    @staticmethod
    def get_by_id(db: Session, company_id: UUID) -> Optional[Company]:
        """Get company by ID."""
        return db.query(Company).filter(Company.id == company_id).first()

    @staticmethod
    def get_by_asx_code(db: Session, asx_code: str) -> Optional[Company]:
        """Get company by ASX code."""
        return db.query(Company).filter(Company.asx_code == asx_code.upper()).first()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get multiple companies with pagination."""
        return db.query(Company).offset(skip).limit(limit).all()

    @staticmethod
    def update(db: Session, company_id: UUID, update_data: dict) -> Optional[Company]:
        """Update a company."""
        company = db.query(Company).filter(Company.id == company_id).first()
        if company:
            for key, value in update_data.items():
                setattr(company, key, value)
            company.last_updated = datetime.utcnow()
            db.commit()
            db.refresh(company)
        return company

    @staticmethod
    def get_or_create(db: Session, asx_code: str, company_name: str) -> Company:
        """
        Get existing company or create new one.

        Args:
            db: Database session
            asx_code: ASX stock code
            company_name: Company name

        Returns:
            Company instance
        """
        company = CompanyService.get_by_asx_code(db, asx_code)
        if not company:
            company = CompanyService.create(
                db,
                {
                    "asx_code": asx_code.upper(),
                    "company_name": company_name,
                },
            )
        return company


class AnalysisService:
    """Service for analysis database operations."""

    @staticmethod
    def create(db: Session, analysis_data: dict) -> Analysis:
        """Create a new analysis."""
        analysis = Analysis(**analysis_data)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def get_by_announcement_id(db: Session, announcement_id: UUID) -> Optional[Analysis]:
        """Get analysis by announcement ID."""
        return db.query(Analysis).filter(Analysis.announcement_id == announcement_id).first()

    @staticmethod
    def update(db: Session, analysis_id: UUID, update_data: dict) -> Optional[Analysis]:
        """Update an analysis."""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            for key, value in update_data.items():
                setattr(analysis, key, value)
            db.commit()
            db.refresh(analysis)
        return analysis


class StockDataService:
    """Service for stock data database operations."""

    @staticmethod
    def create(db: Session, stock_data: dict) -> StockData:
        """Create new stock data record."""
        stock_data_obj = StockData(**stock_data)
        db.add(stock_data_obj)
        db.commit()
        db.refresh(stock_data_obj)
        return stock_data_obj

    @staticmethod
    def get_by_announcement_id(db: Session, announcement_id: UUID) -> List[StockData]:
        """Get all stock data for an announcement."""
        return db.query(StockData).filter(StockData.announcement_id == announcement_id).all()

    @staticmethod
    def get_latest_by_company(db: Session, company_id: UUID) -> Optional[StockData]:
        """Get the most recent stock data for a company."""
        return (
            db.query(StockData)
            .filter(StockData.company_id == company_id)
            .order_by(desc(StockData.fetched_at))
            .first()
        )

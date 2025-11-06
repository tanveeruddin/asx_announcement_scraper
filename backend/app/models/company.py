"""
Company model for ASX listed companies.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Company(Base):
    """ASX listed company model."""

    __tablename__ = "companies"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Company Information
    asx_code = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)

    # Market Data
    market_cap = Column(Numeric(20, 2), nullable=True)  # Market capitalization

    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    announcements = relationship("Announcement", back_populates="company", cascade="all, delete-orphan")
    stock_data = relationship("StockData", back_populates="company", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company(asx_code={self.asx_code}, name={self.company_name})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "asx_code": self.asx_code,
            "company_name": self.company_name,
            "industry": self.industry,
            "market_cap": float(self.market_cap) if self.market_cap else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

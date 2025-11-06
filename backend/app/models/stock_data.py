"""
Stock data model for storing market data and price information.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class StockData(Base):
    """Stock price and market data model."""

    __tablename__ = "stock_data"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    announcement_id = Column(UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)

    # Price Data (at different time points)
    price_at_announcement = Column(Numeric(10, 4), nullable=True)
    price_1h_after = Column(Numeric(10, 4), nullable=True)
    price_1d_after = Column(Numeric(10, 4), nullable=True)
    price_change_pct = Column(Numeric(6, 2), nullable=True)  # Percentage change

    # Volume Data
    volume_at_announcement = Column(BigInteger, nullable=True)

    # Market Metrics
    market_cap = Column(Numeric(20, 2), nullable=True)
    pe_ratio = Column(Numeric(8, 2), nullable=True)

    # Historical Performance (percentage changes)
    performance_1m_pct = Column(Numeric(6, 2), nullable=True)  # 1 month
    performance_3m_pct = Column(Numeric(6, 2), nullable=True)  # 3 months
    performance_6m_pct = Column(Numeric(6, 2), nullable=True)  # 6 months

    # Timestamps
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    announcement = relationship("Announcement", back_populates="stock_data")
    company = relationship("Company", back_populates="stock_data")

    def __repr__(self):
        return f"<StockData(announcement_id={self.announcement_id}, price={self.price_at_announcement})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "announcement_id": str(self.announcement_id),
            "company_id": str(self.company_id),
            "price_at_announcement": float(self.price_at_announcement) if self.price_at_announcement else None,
            "price_1h_after": float(self.price_1h_after) if self.price_1h_after else None,
            "price_1d_after": float(self.price_1d_after) if self.price_1d_after else None,
            "price_change_pct": float(self.price_change_pct) if self.price_change_pct else None,
            "volume_at_announcement": self.volume_at_announcement,
            "market_cap": float(self.market_cap) if self.market_cap else None,
            "pe_ratio": float(self.pe_ratio) if self.pe_ratio else None,
            "performance_1m_pct": float(self.performance_1m_pct) if self.performance_1m_pct else None,
            "performance_3m_pct": float(self.performance_3m_pct) if self.performance_3m_pct else None,
            "performance_6m_pct": float(self.performance_6m_pct) if self.performance_6m_pct else None,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }

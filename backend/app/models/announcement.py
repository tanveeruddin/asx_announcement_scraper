"""
Announcement model for ASX company announcements.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Announcement(Base):
    """ASX company announcement model."""

    __tablename__ = "announcements"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)

    # Announcement Information
    asx_code = Column(String(10), nullable=False, index=True)
    title = Column(Text, nullable=False)
    announcement_date = Column(DateTime, nullable=False, index=True)

    # PDF Information
    pdf_url = Column(Text, nullable=False)
    pdf_local_path = Column(Text, nullable=True)
    markdown_path = Column(Text, nullable=True)

    # Metadata
    is_price_sensitive = Column(Boolean, default=False, nullable=False, index=True)
    num_pages = Column(Integer, nullable=True)
    file_size_kb = Column(Integer, nullable=True)

    # Processing Timestamps
    downloaded_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="announcements")
    analysis = relationship("Analysis", back_populates="announcement", uselist=False, cascade="all, delete-orphan")
    stock_data = relationship("StockData", back_populates="announcement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Announcement(asx_code={self.asx_code}, title={self.title[:50]})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "asx_code": self.asx_code,
            "title": self.title,
            "announcement_date": self.announcement_date.isoformat() if self.announcement_date else None,
            "pdf_url": self.pdf_url,
            "pdf_local_path": self.pdf_local_path,
            "markdown_path": self.markdown_path,
            "is_price_sensitive": self.is_price_sensitive,
            "num_pages": self.num_pages,
            "file_size_kb": self.file_size_kb,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

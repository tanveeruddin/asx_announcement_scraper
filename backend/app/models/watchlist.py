"""
Watchlist model for user company watchlists (future feature).
"""

from datetime import datetime
from sqlalchemy import Column, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Watchlist(Base):
    """User company watchlist model."""

    __tablename__ = "watchlists"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Notification Settings
    notification_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="watchlists")
    company = relationship("Company", back_populates="watchlists")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name='unique_user_company_watchlist'),
    )

    def __repr__(self):
        return f"<Watchlist(user_id={self.user_id}, company_id={self.company_id})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "company_id": str(self.company_id),
            "notification_enabled": self.notification_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

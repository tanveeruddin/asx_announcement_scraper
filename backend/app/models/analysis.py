"""
Analysis model for LLM-powered announcement analysis.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class Analysis(Base):
    """LLM analysis results for announcements."""

    __tablename__ = "analysis"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    announcement_id = Column(UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Analysis Results
    summary = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True, index=True)  # 'bullish', 'bearish', 'neutral'
    key_insights = Column(JSONB, nullable=True)  # Array of insights as JSON
    financial_impact = Column(Text, nullable=True)  # LLM's assessment of financial impact

    # LLM Metadata
    llm_model = Column(String(50), nullable=True)  # 'gemini-1.5-pro', etc.
    llm_prompt_version = Column(String(50), nullable=True)  # Track prompt versions
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    processing_time_ms = Column(Integer, nullable=True)  # Processing time in milliseconds

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    announcement = relationship("Announcement", back_populates="analysis")

    def __repr__(self):
        return f"<Analysis(announcement_id={self.announcement_id}, sentiment={self.sentiment})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "announcement_id": str(self.announcement_id),
            "summary": self.summary,
            "sentiment": self.sentiment,
            "key_insights": self.key_insights,
            "financial_impact": self.financial_impact,
            "llm_model": self.llm_model,
            "llm_prompt_version": self.llm_prompt_version,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

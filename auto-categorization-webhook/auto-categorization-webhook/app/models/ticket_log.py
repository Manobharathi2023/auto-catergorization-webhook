"""
SQLAlchemy model for ticket classification logs.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database.connection import Base


class TicketLog(Base):
    """Model to store all ticket classification logs for monitoring."""
    __tablename__ = "ticket_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(100), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    processing_time = Column(Float, nullable=True)  # in milliseconds
    attempts = Column(Integer, default=1)
    agent_reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "priority": self.priority,
            "confidence": self.confidence,
            "model_used": self.model_used,
            "processing_time_ms": self.processing_time,
            "attempts": self.attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""
Service layer for ticket database operations and monitoring statistics.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ticket_log import TicketLog

logger = logging.getLogger(__name__)


class TicketService:
    """Service for managing ticket log persistence and retrieval."""

    def save_classification(self, db: Session, classification_result: dict, title: str, description: Optional[str] = None) -> TicketLog:
        """Save a classification result to the database."""
        try:
            log = TicketLog(
                ticket_id=classification_result["ticket_id"],
                title=title,
                description=description,
                category=classification_result.get("category"),
                subcategory=classification_result.get("subcategory"),
                priority=classification_result.get("priority"),
                confidence=classification_result.get("confidence"),
                model_used=classification_result.get("model_used"),
                processing_time=classification_result.get("processing_time_ms"),
                attempts=classification_result.get("attempts", 1),
                agent_reasoning=classification_result.get("agent_reasoning"),
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            logger.info(f"Saved classification log for ticket: {classification_result['ticket_id']}")
            return log
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving classification: {e}")
            raise

    def get_monitoring_stats(self, db: Session) -> dict:
        """Get monitoring statistics from the database."""
        try:
            total = db.query(func.count(TicketLog.id)).scalar() or 0
            avg_confidence = db.query(func.avg(TicketLog.confidence)).scalar() or 0.0

            # Category distribution
            category_rows = (
                db.query(TicketLog.category, func.count(TicketLog.id))
                .group_by(TicketLog.category)
                .all()
            )
            category_dist = {row[0]: row[1] for row in category_rows if row[0]}

            # Priority distribution
            priority_rows = (
                db.query(TicketLog.priority, func.count(TicketLog.id))
                .group_by(TicketLog.priority)
                .all()
            )
            priority_dist = {row[0]: row[1] for row in priority_rows if row[0]}

            # Recent 10 tickets
            recent = db.query(TicketLog).order_by(TicketLog.created_at.desc()).limit(10).all()
            recent_list = [t.to_dict() for t in recent]

            return {
                "total_tickets": total,
                "average_confidence": round(float(avg_confidence), 3),
                "category_distribution": category_dist,
                "priority_distribution": priority_dist,
                "recent_tickets": recent_list,
            }
        except Exception as e:
            logger.error(f"Error fetching monitoring stats: {e}")
            raise

    def get_all_logs(self, db: Session, skip: int = 0, limit: int = 100) -> list:
        """Get paginated list of all ticket logs."""
        return db.query(TicketLog).order_by(TicketLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_log_by_ticket_id(self, db: Session, ticket_id: str) -> Optional[TicketLog]:
        """Get the latest log entry for a specific ticket ID."""
        return (
            db.query(TicketLog)
            .filter(TicketLog.ticket_id == ticket_id)
            .order_by(TicketLog.created_at.desc())
            .first()
        )


# Singleton instance
ticket_service = TicketService()

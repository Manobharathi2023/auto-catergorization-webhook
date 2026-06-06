"""
FastAPI route handlers for ticket classification and monitoring.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.ticket import TicketRequest, ClassificationResponse, LogsResponse, HealthResponse
from app.agents.classification_agent import classification_agent
from app.services.ticket_service import ticket_service
from app.services.ollama_service import ollama_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/classify",
    response_model=ClassificationResponse,
    summary="Classify a support ticket",
    description="Receives a support ticket and returns AI-powered classification with category, subcategory, priority, and confidence score."
)
async def classify_ticket(ticket: TicketRequest, db: Session = Depends(get_db)):
    """
    Classify a support ticket using the AI agent loop.
    
    The agent will:
    1. Build few-shot prompt with training examples
    2. Call Ollama LLM for classification
    3. Evaluate confidence score
    4. Retry up to 3 times if confidence is low
    5. Return enriched classification result
    """
    logger.info(f"Received classification request for ticket: {ticket.ticket_id}")

    try:
        # Run agent classification loop
        result = await classification_agent.classify_ticket(
            ticket_id=ticket.ticket_id,
            title=ticket.title,
            description=ticket.description
        )

        # Persist to database
        ticket_service.save_classification(db, result, ticket.title, ticket.description)

        logger.info(
            f"Classification complete: {ticket.ticket_id} -> "
            f"{result['category']}/{result['subcategory']} "
            f"(confidence: {result['confidence']:.2f})"
        )
        return ClassificationResponse(**result)

    except Exception as e:
        logger.error(f"Classification error for {ticket.ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.get(
    "/logs",
    response_model=LogsResponse,
    summary="Get monitoring statistics",
    description="Returns aggregated statistics: total tickets processed, average confidence, category distribution, priority distribution, and recent tickets."
)
def get_logs(db: Session = Depends(get_db)):
    """Get monitoring and analytics data from ticket classification logs."""
    try:
        stats = ticket_service.get_monitoring_stats(db)
        return LogsResponse(**stats)
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch logs: {str(e)}")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API, Ollama connection, and database."
)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify all services are running."""
    ollama_ok = await ollama_service.is_available()

    # Check database
    db_ok = True
    try:
        from app.models.ticket_log import TicketLog
        db.query(TicketLog).limit(1).all()
    except Exception:
        db_ok = False

    from app.services.ollama_service import PRIMARY_MODEL
    return HealthResponse(
        status="healthy" if (ollama_ok and db_ok) else "degraded",
        ollama_available=ollama_ok,
        database_connected=db_ok,
        model=PRIMARY_MODEL
    )


@router.get(
    "/tickets/{ticket_id}",
    summary="Get ticket classification history",
    description="Retrieve the most recent classification result for a specific ticket ID."
)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Get classification history for a specific ticket."""
    log = ticket_service.get_log_by_ticket_id(db, ticket_id)
    if not log:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return log.to_dict()

"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TicketRequest(BaseModel):
    """Input schema for ticket classification request."""
    ticket_id: str = Field(..., description="Unique identifier for the ticket", example="TKT-001")
    title: str = Field(..., min_length=1, description="Ticket title/subject", example="Unable to login")
    description: Optional[str] = Field(
        None,
        description="Detailed description of the issue",
        example="User cannot access portal after password reset"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TKT-001",
                "title": "Unable to login",
                "description": "User cannot access portal after password reset"
            }
        }


class ClassificationResponse(BaseModel):
    """Output schema for ticket classification response."""
    ticket_id: str
    category: str
    subcategory: str
    priority: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_used: str
    processing_time_ms: float
    timestamp: datetime
    attempts: int = Field(default=1, description="Number of classification attempts made")
    agent_reasoning: Optional[str] = Field(None, description="Agent's reasoning steps")

    class Config:
        json_schema_extra = {
            "example": {
                "ticket_id": "TKT-001",
                "category": "Authentication",
                "subcategory": "Login Failure",
                "priority": "High",
                "confidence": 0.93,
                "model_used": "llama3",
                "processing_time_ms": 1200,
                "timestamp": "2026-01-01T12:00:00",
                "attempts": 1
            }
        }


class LogsResponse(BaseModel):
    """Response schema for monitoring logs endpoint."""
    total_tickets: int
    average_confidence: float
    category_distribution: dict
    priority_distribution: dict
    recent_tickets: list


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    ollama_available: bool
    database_connected: bool
    model: str

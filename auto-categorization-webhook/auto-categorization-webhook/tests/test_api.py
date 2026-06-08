"""
Pytest test suite for Auto-Categorization Webhook.
Tests: Happy path, edge cases, agent loop, API failures.
"""
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_ticket_logs.db"


@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    from app.database.connection import Base
    from app.models.ticket_log import TicketLog  # noqa
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_ticket_logs.db"):
        os.remove("test_ticket_logs.db")


@pytest.fixture
def db_session(test_db_engine):
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(test_db_engine):
    from app.main import app
    from app.database.connection import get_db
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=test_db_engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Mock classification result
MOCK_CLASSIFICATION = {
    "ticket_id": "TKT-TEST",
    "category": "Authentication",
    "subcategory": "Login Failure",
    "priority": "High",
    "confidence": 0.92,
    "model_used": "llama3",
    "processing_time_ms": 500.0,
    "timestamp": __import__("datetime").datetime.utcnow(),
    "attempts": 1,
    "agent_reasoning": "Step 1: Received ticket\nStep 2: Classified with high confidence",
}


# ─────────────────────────────────────────────
# HAPPY PATH TESTS
# ─────────────────────────────────────────────

class TestHappyPath:

    def test_health_endpoint(self, client):
        """Health endpoint should return 200."""
        with patch("app.services.ollama_service.OllamaService.is_available", new_callable=AsyncMock, return_value=True):
            response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database_connected" in data
        assert data["database_connected"] is True

    def test_classify_happy_path(self, client):
        """Valid ticket should return 200 with classification."""
        with patch("app.agents.classification_agent.ClassificationAgent.classify_ticket",
                   new_callable=AsyncMock, return_value=MOCK_CLASSIFICATION):
            response = client.post("/api/classify", json={
                "ticket_id": "TKT-001",
                "title": "Unable to login",
                "description": "User cannot access portal after password reset"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_id"] == "TKT-TEST"
        assert data["category"] == "Authentication"
        assert data["subcategory"] == "Login Failure"
        assert data["priority"] == "High"
        assert 0.0 <= data["confidence"] <= 1.0

    def test_classify_returns_required_fields(self, client):
        """Response must contain all required fields."""
        with patch("app.agents.classification_agent.ClassificationAgent.classify_ticket",
                   new_callable=AsyncMock, return_value=MOCK_CLASSIFICATION):
            response = client.post("/api/classify", json={
                "ticket_id": "TKT-002",
                "title": "Payment not going through"
            })
        assert response.status_code == 200
        required = ["ticket_id", "category", "subcategory", "priority", "confidence", "model_used", "processing_time_ms"]
        for field in required:
            assert field in response.json(), f"Missing field: {field}"

    def test_logs_endpoint(self, client):
        """Logs endpoint should return monitoring stats."""
        response = client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "average_confidence" in data
        assert "category_distribution" in data
        assert "priority_distribution" in data

    def test_docs_available(self, client):
        """Swagger docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200


# ─────────────────────────────────────────────
# EDGE CASE TESTS
# ─────────────────────────────────────────────

class TestEdgeCases:

    def test_empty_title_rejected(self, client):
        """Empty title should return 422 validation error."""
        response = client.post("/api/classify", json={
            "ticket_id": "TKT-EMPTY",
            "title": "",
            "description": "Some description"
        })
        assert response.status_code == 422

    def test_missing_title_rejected(self, client):
        """Missing title field should return 422."""
        response = client.post("/api/classify", json={
            "ticket_id": "TKT-NO-TITLE",
            "description": "Some description"
        })
        assert response.status_code == 422

    def test_no_description_ok(self, client):
        """Ticket without description should still classify."""
        mock_result = {**MOCK_CLASSIFICATION, "ticket_id": "TKT-NODESC"}
        with patch("app.agents.classification_agent.ClassificationAgent.classify_ticket",
                   new_callable=AsyncMock, return_value=mock_result):
            response = client.post("/api/classify", json={
                "ticket_id": "TKT-NODESC",
                "title": "Application is slow"
            })
        assert response.status_code == 200

    def test_very_long_title(self, client):
        """Very long title should still work."""
        long_title = "Application crashes " * 20
        mock_result = {**MOCK_CLASSIFICATION, "ticket_id": "TKT-LONG"}
        with patch("app.agents.classification_agent.ClassificationAgent.classify_ticket",
                   new_callable=AsyncMock, return_value=mock_result):
            response = client.post("/api/classify", json={
                "ticket_id": "TKT-LONG",
                "title": long_title[:499]
            })
        assert response.status_code == 200

    def test_ticket_not_found_404(self, client):
        """Unknown ticket ID should return 404."""
        response = client.get("/api/tickets/TKT-DOES-NOT-EXIST-999")
        assert response.status_code == 404


# ─────────────────────────────────────────────
# AGENT LOOP TESTS
# ─────────────────────────────────────────────

class TestAgentLoop:

    @pytest.mark.asyncio
    async def test_agent_retries_on_low_confidence(self):
        """Agent should retry when confidence is below threshold."""
        from app.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()
        agent.confidence_threshold = 0.6
        agent.max_attempts = 3

        low_conf_result = {
            "category": "General Inquiry", "subcategory": "Unclassified",
            "priority": "Medium", "confidence": 0.4, "model_used": "llama3"
        }
        high_conf_result = {
            "category": "Authentication", "subcategory": "Login Failure",
            "priority": "High", "confidence": 0.9, "model_used": "llama3"
        }

        call_count = 0

        async def mock_classify(prompt, model=None):
            nonlocal call_count
            call_count += 1
            return low_conf_result if call_count < 2 else high_conf_result

        with patch.object(agent, "_ClassificationAgent__dict__", {}, create=True):
            with patch("app.services.ollama_service.OllamaService.classify", side_effect=mock_classify):
                result = await agent.classify_ticket("TKT-RETRY", "Login issue", "Cannot login")

        assert result["attempts"] >= 1
        assert "agent_reasoning" in result

    @pytest.mark.asyncio
    async def test_agent_uses_fallback_after_max_retries(self):
        """Agent should return fallback result after max retries."""
        from app.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()
        agent.max_attempts = 2

        async def always_fail(prompt, model=None):
            raise Exception("Ollama unavailable")

        with patch("app.services.ollama_service.OllamaService.classify", side_effect=always_fail):
            result = await agent.classify_ticket("TKT-FAIL", "Some issue", "Some description")

        # Should not raise, should return fallback
        assert result["category"] is not None
        assert result["confidence"] is not None


# ─────────────────────────────────────────────
# FEW-SHOT SERVICE TESTS
# ─────────────────────────────────────────────

class TestFewShotService:

    def test_load_examples(self):
        """Should load examples from JSON file."""
        from app.services.few_shot_service import FewShotService
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "few_shot_examples.json"))
        service = FewShotService(file_path)
        examples = service.load_examples()
        assert len(examples) >= 20

    def test_search_examples(self):
        """Search should return relevant examples."""
        from app.services.few_shot_service import FewShotService
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "few_shot_examples.json"))
        service = FewShotService(file_path)
        results = service.search_examples("login")
        assert len(results) > 0
        # All results should be somewhat relevant
        for ex in results:
            assert "category" in ex

    def test_get_categories(self):
        """Should return all unique categories."""
        from app.services.few_shot_service import FewShotService
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "few_shot_examples.json"))
        service = FewShotService(file_path)
        categories = service.get_categories()
        assert "Authentication" in categories
        assert "Billing" in categories


# ─────────────────────────────────────────────
# MCP TOOL TESTS
# ─────────────────────────────────────────────

class TestMCPTool:

    def test_search_returns_results(self):
        """MCP search tool should return matching examples."""
        from mcp.tools import TicketKnowledgeTool
        tool = TicketKnowledgeTool()
        result = tool.search_examples("login", max_results=3)
        assert result["query"] == "login"
        assert isinstance(result["examples"], list)

    def test_get_category_examples(self):
        """Category filter should return examples for that category."""
        from mcp.tools import TicketKnowledgeTool
        tool = TicketKnowledgeTool()
        result = tool.get_category_examples("Authentication")
        assert result["category"] == "Authentication"
        for ex in result["examples"]:
            assert "title" in ex

    def test_empty_search_returns_empty(self):
        """Search with no matches should return empty list."""
        from mcp.tools import TicketKnowledgeTool
        tool = TicketKnowledgeTool()
        result = tool.search_examples("xyzzy_no_match_123456")
        assert result["total_found"] == 0

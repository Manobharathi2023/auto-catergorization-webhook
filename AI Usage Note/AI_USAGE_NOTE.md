# AI Usage Note

**Team 15 | Challenge SD-02 | Auto-Categorization Webhook**

---

## What AI Helped With

### 1. Architecture Design
- Suggested the Agent Loop pattern for retry-based confidence improvement
- Recommended FastAPI + SQLAlchemy + SQLite as the production-ready stack
- Proposed the MCP server using stdio/HTTP transport for flexibility

### 2. Prompt Engineering
- Generated the initial zero-shot classification prompt
- Helped refine few-shot examples for better coverage across categories
- Suggested adding a `reasoning` field to make agent decisions auditable
- Advised on temperature=0.1 for deterministic JSON output

### 3. Code Generation
- Generated boilerplate for FastAPI routes with proper error handling
- Helped write the JSON parsing pipeline with multiple fallback strategies
- Created the Chart.js integration for the monitoring dashboard
- Generated the pytest test structure including edge cases

### 4. Documentation
- Helped structure the README with Mermaid architecture diagram
- Generated comprehensive API documentation strings
- Assisted with the prompts.md iteration history

---

## What AI Got Wrong

### 1. Over-engineered Initial Architecture
- Initially suggested using Redis for caching — overkill for this scope
- Proposed Celery for async task queue — unnecessary given FastAPI's async support
- **Fix:** Kept it simple with SQLite + FastAPI async handlers

### 2. MCP Implementation Complexity
- Suggested using a third-party MCP SDK that wasn't available
- Tried to add authentication to the MCP server unnecessarily
- **Fix:** Implemented simple JSON-RPC over HTTP for ease of use and testing

### 3. Prompt Hallucination Issues
- Initial prompts caused the LLM to invent new category names
- Confidence scores were often over-inflated (0.95+) even for borderline cases
- **Fix:** Added explicit category list to prompt and calibrated with retry threshold

### 4. Docker Compose Complexity
- Initially generated a docker-compose with PostgreSQL — violates free tools requirement
- Suggested multi-stage Docker builds unnecessarily
- **Fix:** Simplified to SQLite (no separate DB container needed)

---

## Best Prompts Used

### For Code Generation:
```
"Write a FastAPI async route that receives a Pydantic model, 
calls an async agent, saves to SQLAlchemy ORM, and returns 
a typed Pydantic response. Include proper error handling with 
HTTPException and logging."
```

### For Architecture:
```
"Design an AI agent loop for ticket classification that:
1. Tries up to 3 times if confidence < 0.6
2. Uses different prompts on each attempt
3. Returns reasoning steps for debugging
4. Falls back gracefully if LLM is unavailable"
```

### For Tests:
```
"Write pytest tests for a FastAPI ticket classification API covering:
happy path, empty title, missing description, very long input, 
404 for unknown ticket, and agent retry behavior.
Use AsyncMock for Ollama calls and in-memory SQLite for the database."
```

---

## Improvements Made Based on AI Output

| AI Suggestion | Issue | Our Fix |
|---------------|-------|---------|
| Use OpenAI API | Costs money | Used Ollama (free, local) |
| Redis caching | Over-complex | In-memory Python dict |
| JWT auth | Out of scope | Removed entirely |
| Multiple DB tables | Complexity | Single `ticket_logs` table |
| Celery workers | Overkill | FastAPI async is sufficient |

---

## AI Tools Used

- **Claude (Anthropic)** — Primary assistant for architecture, code, and documentation
- **GitHub Copilot** — Inline code completion during development

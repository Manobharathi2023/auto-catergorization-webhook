# 🎫 Auto-Categorization Webhook

> **Team 15 | Challenge SD-02 | Hackathon Project**

AI-powered support ticket classification service using Few-Shot Prompting, Agent Loop, and MCP tooling.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20llama3-orange)](https://ollama.ai)
[![SQLite](https://img.shields.io/badge/DB-SQLite-lightgrey)](https://sqlite.org)

---

## 📋 Problem Statement

Manual ticket tagging is slow, inconsistent, and error-prone. Support teams waste time on repetitive categorization instead of solving problems. This service automates ticket classification with AI, returning structured category/subcategory/priority data in milliseconds.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    Client([Client / Dashboard]) --> API[FastAPI\n/api/classify]
    API --> Agent[Classification Agent\nAgent Loop]
    Agent --> Prompt[Prompt Builder\nFew-Shot Templates]
    Prompt --> Ollama[Ollama LLM\nllama3 / mistral]
    Ollama --> Eval{Confidence\n>= 0.6?}
    Eval -- Yes --> DB[(SQLite\nticket_logs)]
    Eval -- No, attempt < 3 --> Retry[Retry Prompt]
    Retry --> Ollama
    Eval -- No, attempt = 3 --> Fallback[Fallback Prompt]
    Fallback --> DB
    DB --> Response[Enriched JSON\nResponse]
    
    MCP[MCP Server\n:8001] --> FewShot[Few-Shot\nExamples JSON]
    Agent --> MCP
    
    Monitor[/api/logs] --> DB
    Dashboard[Frontend\nDashboard] --> API
    Dashboard --> Monitor
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Agent Loop** | Retries classification up to 3× when confidence < 0.6 |
| 📚 **Few-Shot Learning** | 22 labeled examples across 6 categories |
| 🔍 **MCP Tool Server** | Ticket knowledge search via Model Context Protocol |
| 📊 **Monitoring Dashboard** | Real-time category/priority charts with Chart.js |
| 🗄️ **SQLite Logging** | Every prediction stored for audit and monitoring |
| 🐳 **Docker Ready** | One command to run everything |
| 🧪 **Full Test Suite** | Pytest with happy path and edge cases |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- llama3 model pulled: `ollama pull llama3`

### Option 1: Local Development (VSCode)

```bash
# 1. Clone and setup
git clone <repo-url>
cd auto-categorization-webhook

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Start Ollama (in a separate terminal)
ollama serve
ollama pull llama3

# 6. Run the API
uvicorn app.main:app --reload

# 7. Open dashboard
open http://localhost:8000
```

### Option 2: Docker (One Command)

```bash
docker-compose up --build
```

This starts:
- FastAPI backend on `http://localhost:8000`
- MCP server on `http://localhost:8001`
- Ollama service on `http://localhost:11434`

> ⚠️ First run pulls `llama3` model (~4GB). Allow 5-10 minutes.

---

## 📡 API Usage

### POST /api/classify

Classify a support ticket.

```bash
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "TKT-001",
    "title": "Unable to login",
    "description": "User cannot access portal after password reset"
  }'
```

**Response:**
```json
{
  "ticket_id": "TKT-001",
  "category": "Authentication",
  "subcategory": "Login Failure",
  "priority": "High",
  "confidence": 0.93,
  "model_used": "llama3",
  "processing_time_ms": 1200,
  "timestamp": "2026-01-01T12:00:00",
  "attempts": 1,
  "agent_reasoning": "Step 1: Received ticket...\nStep 2: High confidence - accepting"
}
```

### GET /api/logs

Get monitoring statistics.

```bash
curl http://localhost:8000/api/logs
```

### GET /api/health

Check service health.

```bash
curl http://localhost:8000/api/health
```

### GET /api/tickets/{ticket_id}

Get classification history for a ticket.

```bash
curl http://localhost:8000/api/tickets/TKT-001
```

---

## 🔌 MCP Server Usage

The MCP server exposes ticket knowledge search tools.

### HTTP Mode (for testing)

```bash
# Start MCP server
python mcp/server.py --transport http --port 8001

# Search examples
curl -X POST http://localhost:8001 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_ticket_examples",
      "arguments": {"query": "login issue", "max_results": 3}
    }
  }'
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `search_ticket_examples` | Search historical tickets by keyword |
| `get_category_examples` | Get all examples for a category |

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --tb=short
```

**Test Coverage:**
- ✅ Happy path classification
- ✅ Empty/missing title validation
- ✅ No description handling
- ✅ Long title handling
- ✅ 404 for unknown ticket
- ✅ Agent retry loop
- ✅ Fallback on LLM failure
- ✅ Few-shot service loading
- ✅ MCP tool search

---

## 📁 Project Structure

```
auto-categorization-webhook/
├── app/
│   ├── agents/
│   │   └── classification_agent.py   # AI Agent Loop
│   ├── api/
│   │   └── routes.py                 # FastAPI routes
│   ├── database/
│   │   └── connection.py             # SQLAlchemy setup
│   ├── models/
│   │   └── ticket_log.py             # DB model
│   ├── prompts/
│   │   └── classification_prompts.py # Prompt templates
│   ├── schemas/
│   │   └── ticket.py                 # Pydantic schemas
│   ├── services/
│   │   ├── few_shot_service.py       # Example loader
│   │   ├── ollama_service.py         # LLM client
│   │   └── ticket_service.py         # DB operations
│   └── main.py                       # FastAPI app
├── mcp/
│   ├── server.py                     # MCP Server
│   └── tools.py                      # MCP Tools
├── frontend/
│   ├── index.html                    # Dashboard UI
│   ├── style.css                     # Dark theme CSS
│   └── app.js                        # Chart.js + API calls
├── data/
│   └── few_shot_examples.json        # 22 training examples
├── tests/
│   └── test_api.py                   # Pytest test suite
├── docs/
│   └── prompts.md                    # Prompt engineering docs
├── sample_data/
│   ├── sample_input.json
│   └── sample_output.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── AI_USAGE_NOTE.md
└── README.md
```

---

## 🏷️ Classification Categories

| Category | Subcategories | Typical Priority |
|----------|--------------|-----------------|
| Authentication | Login Failure, Password Reset, MFA Issue, SSO Issue | High–Critical |
| Billing | Refund, Payment Failure, Invoice Dispute, Subscription | High |
| Technical | Bug, Performance, Sync Issue, API Issue, Notification | Medium–Critical |
| Network | VPN, Connectivity, Network Performance | Medium–High |
| Account | Profile Update, Access Request, Account Lockout | Low–High |
| General Inquiry | How-To, Software Request | Low |

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and adjust:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `PRIMARY_MODEL` | `llama3` | Primary LLM model |
| `FALLBACK_MODEL` | `mistral` | Fallback LLM model |
| `CONFIDENCE_THRESHOLD` | `0.6` | Retry threshold |
| `DATABASE_URL` | `sqlite:///./ticket_logs.db` | Database path |

---

## 📷 Screenshots

> Dashboard, API docs, and sample classifications available in `/sample_data/`

| Page | URL |
|------|-----|
| Dashboard | http://localhost:8000 |
| Swagger API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| MCP Health | http://localhost:8001/health |

---

## 🔮 Assumptions

1. Ollama is installed and accessible at the configured URL
2. llama3 model is pulled before first classification
3. Single-user deployment (no authentication required)
4. SQLite is sufficient for hackathon scale

## ⚠️ Limitations

1. Classification quality depends on Ollama model quality
2. Cold start: first classification takes longer as model loads
3. No real-time streaming of classification progress
4. MCP search uses keyword matching, not semantic similarity

## 🚧 Future Enhancements

- [ ] Vector embeddings for semantic MCP search
- [ ] Webhook notifications to ticketing systems (Jira, ServiceNow)
- [ ] Multi-language support
- [ ] Fine-tuned classification model
- [ ] Real-time WebSocket updates for live classification status
- [ ] Batch classification endpoint
- [ ] A/B testing between models

---

## 👥 Team

**Team 15** — Challenge SD-02: Auto-Categorization Webhook

"""
Auto-Categorization Webhook - Main FastAPI Application
Team 15 | Challenge SD-02
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.database.connection import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Starting Auto-Categorization Webhook Service...")
    init_db()
    logger.info("Database initialized successfully")
    logger.info("Service ready to accept requests")
    yield
    # Shutdown
    logger.info("Shutting down Auto-Categorization Webhook Service...")


app = FastAPI(
    title="Auto-Categorization Webhook",
    description="""
## AI-Powered Support Ticket Classification Service

**Team 15 | Challenge SD-02**

This service automatically classifies support tickets using AI-powered few-shot learning.

### Features
- 🤖 **AI Agent Loop**: Intelligent retry mechanism with confidence evaluation
- 📊 **Few-Shot Classification**: 20+ training examples for accurate classification
- 🔍 **MCP Tool Support**: Ticket knowledge search via MCP server
- 📈 **Monitoring**: Real-time stats and category distribution
- 🗄️ **Persistence**: All predictions logged in SQLite for audit trail

### Classification Categories
- **Authentication**: Login failures, password resets, MFA issues, SSO
- **Billing**: Refunds, payment failures, invoice disputes, subscriptions
- **Technical**: Bugs, performance issues, API issues, sync problems
- **Network**: VPN, connectivity, network performance
- **Account**: Profile updates, access requests, account lockouts
- **General Inquiry**: How-to questions, software requests
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix="/api", tags=["Classification API"])

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

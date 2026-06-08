#!/bin/bash
# ============================================================
# Auto-Categorization Webhook - VSCode Startup Script
# Team 15 | Challenge SD-02
# ============================================================

set -e

echo "============================================================"
echo "  Auto-Categorization Webhook - Team 15"
echo "============================================================"

# Check Python version
echo "Checking Python version..."
python3 --version || { echo "ERROR: Python 3 not found"; exit 1; }

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || true

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Copy .env if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

# Check Ollama
echo ""
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Ollama is running!"
    echo "Pulling llama3 model (if not already downloaded)..."
    ollama pull llama3 || echo "Note: Could not pull llama3. Run 'ollama pull llama3' manually."
else
    echo ""
    echo "WARNING: Ollama not detected at http://localhost:11434"
    echo "  Install Ollama: https://ollama.ai"
    echo "  Then run: ollama serve && ollama pull llama3"
    echo "  The API will start but classification will fail without Ollama."
    echo ""
fi

# Start MCP server in background
echo "Starting MCP server on port 8001..."
python mcp/server.py --transport http --port 8001 &
MCP_PID=$!
echo "MCP server PID: $MCP_PID"

# Start FastAPI
echo ""
echo "============================================================"
echo "  Starting FastAPI server on http://localhost:8000"
echo "  Dashboard:    http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  MCP Server:   http://localhost:8001"
echo "============================================================"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Cleanup on exit
kill $MCP_PID 2>/dev/null || true

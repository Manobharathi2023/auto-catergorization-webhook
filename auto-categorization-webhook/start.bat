@echo off
echo ============================================================
echo   Auto-Categorization Webhook - Team 15
echo ============================================================

echo Checking Python...
python --version || (echo ERROR: Python not found && pause && exit /b 1)

echo Creating virtual environment...
if not exist venv (
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

if not exist .env (
    copy .env.example .env
    echo Created .env from .env.example
)

echo.
echo Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% == 0 (
    echo Ollama is running!
) else (
    echo WARNING: Ollama not detected.
    echo Install from: https://ollama.ai
    echo Then run: ollama serve ^&^& ollama pull llama3
    echo.
)

echo Starting MCP server on port 8001...
start /B python mcp/server.py --transport http --port 8001

echo.
echo ============================================================
echo   Starting FastAPI server on http://localhost:8000
echo   Dashboard:    http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo   MCP Server:   http://localhost:8001
echo ============================================================
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause

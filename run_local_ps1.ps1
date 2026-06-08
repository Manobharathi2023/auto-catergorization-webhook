# PowerShell runner for local FastAPI + Ollama (no Docker)
# Fixes common path/import issues on Windows.

$ErrorActionPreference = "Stop"

$ProjectRoot = "d:\Infinite SDE Project-1\auto-categorization-webhook"
$Env:PYTHONPATH = $ProjectRoot

Write-Host "Starting FastAPI on http://127.0.0.1:8000 ..."
cd $ProjectRoot

# If you want hot-reload, keep --reload
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000


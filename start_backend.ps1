# =============================================
# UEBA SHIELD — Backend API Service
# Port: 8000
# =============================================
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  UEBA SHIELD :: Backend API (Port 8000)" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[START] Activating virtual environment..." -ForegroundColor Yellow

Set-Location "$PSScriptRoot\backend"

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "[OK]    Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "[WARN]  No venv found. Attempting to run without activation." -ForegroundColor Yellow
}

Write-Host "[START] Launching Backend API with uvicorn..." -ForegroundColor Yellow
Write-Host ""
& ".\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

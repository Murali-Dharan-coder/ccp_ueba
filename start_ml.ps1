# =============================================
# UEBA SHIELD — ML Anomaly Detection Service
# Port: 8001
# =============================================
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host "  UEBA SHIELD :: ML Service (Port 8001)  " -ForegroundColor Magenta
Write-Host "=========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "[START] Activating virtual environment..." -ForegroundColor Yellow

Set-Location "$PSScriptRoot\ueba - ml"

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "[OK]    Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "[WARN]  No venv found. Attempting to run without activation." -ForegroundColor Yellow
}

Write-Host "[START] Launching ML Anomaly Service with uvicorn..." -ForegroundColor Yellow
Write-Host ""
& ".\venv\Scripts\python.exe" -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

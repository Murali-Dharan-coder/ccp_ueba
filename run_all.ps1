# ============================================================
# UEBA SHIELD — Combined Service Launcher
# Runs ALL services together in background processes.
# Tip: Use start_backend.ps1 / start_ml.ps1 for individual
#      service launches with live logs.
# ============================================================

$Root = $PSScriptRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  UEBA SHIELD :: Full Stack Launcher                        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. ML Anomaly Detection Service (Port 8001) ──────────────
Write-Host "[1/3] Starting ML Service (Port 8001)..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$Root\ueba - ml'; & '.\venv\Scripts\python.exe' -m uvicorn app:app --host 0.0.0.0 --port 8001`"" -WindowStyle Normal
Start-Sleep -Seconds 2

# ── 2. Backend API (Port 8000) ───────────────────────────────
Write-Host "[2/3] Starting Backend API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$Root\backend'; & '.\venv\Scripts\python.exe' -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`"" -WindowStyle Normal
Start-Sleep -Seconds 2

# ── 3. Frontend HTTP Server (Port 8080) ──────────────────────
Write-Host "[3/3] Starting Frontend Server (Port 8080)..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit -Command `"python -m http.server 8080 --directory '$Root\frontend'`"" -WindowStyle Normal

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  All services launched in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "  Admin Portal  : http://localhost:8080/admin/index.html" -ForegroundColor White
Write-Host "  Employee Portal: http://localhost:8080/employee/index.html" -ForegroundColor White
Write-Host ""
Write-Host "  Admin PIN     : 230806" -ForegroundColor Yellow
Write-Host "  Employee Login: e.g. E001 / password123" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

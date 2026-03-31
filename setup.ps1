# Setup Script for Hybrid UEBA Project

Write-Host "--- Starting Hybrid UEBA Setup ---" -ForegroundColor Cyan

# 1. Setup Backend Environment
Write-Host "`n[1/2] Setting up Backend..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "Existing backend venv found. Skipping creation."
} else {
    python -m venv backend\venv
}
& "backend\venv\Scripts\pip" install -r backend\requirements.txt

# 2. Setup ML Service Environment
Write-Host "`n[2/2] Setting up ML Service..." -ForegroundColor Yellow
if (Test-Path "ueba - ml\venv") {
    Write-Host "Existing ML venv found. Skipping creation."
} else {
    python -m venv "ueba - ml\venv"
}
& "ueba - ml\venv\Scripts\pip" install -r "ueba - ml\requirement.txt"

Write-Host "`n--- Setup Complete! ---" -ForegroundColor Green
Write-Host "You can now run the application using run_all.ps1 (to be created next)."

# Sales & Operations Intelligence Dashboard Launcher (PowerShell)
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Starting Sales & Operations Intelligence Dashboard (Local Server)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan

$ProjectDir = $PSScriptRoot

# 1. Start Backend in a new window
Write-Host "`n[1/2] Starting Backend (FastAPI) on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir\backend'; python run.py"

Start-Sleep -Seconds 3

# 2. Start Frontend in a new window
Write-Host "[2/2] Starting Frontend (React + Vite) on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$ProjectDir\frontend'; npm run dev"

Start-Sleep -Seconds 2

Write-Host "`nOpening http://localhost:5173 in browser..." -ForegroundColor Green
Start-Process "http://localhost:5173"

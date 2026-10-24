@echo off
title Sales ^& Operations Intelligence Dashboard Launcher
color 0A

echo ======================================================================
echo    Starting Sales ^& Operations Intelligence Dashboard (Local Server)
echo ======================================================================
echo.

:: Get project root directory
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [1/3] Checking dependencies...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b 1
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH! Please install Node.js 18+.
    pause
    exit /b 1
)

echo [2/3] Launching FastAPI Backend on http://localhost:8000 ...
start "Backend Server (FastAPI)" cmd /k "cd /d "%PROJECT_DIR%backend" && python run.py"

:: Brief pause to let backend initialize
timeout /t 3 /nobreak >nul

echo [3/3] Launching React Frontend on http://localhost:5173 ...
start "Frontend Server (Vite + React)" cmd /k "cd /d "%PROJECT_DIR%frontend" && npm run dev"

echo.
echo ======================================================================
echo    Servers are starting in separate windows!
echo.
echo    - Frontend Dashboard:  http://localhost:5173
echo    - Backend REST API:    http://localhost:8000
echo    - Interactive API Docs: http://localhost:8000/docs
echo.
echo    Press any key to open the dashboard in your default browser...
echo ======================================================================
pause >nul

start http://localhost:5173

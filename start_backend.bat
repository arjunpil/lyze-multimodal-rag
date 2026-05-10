@echo off
title Lyze Backend
color 0B
cd /d "%~dp0backend"

echo.
echo  ==========================================
echo    Lyze Backend
echo    http://localhost:8000
echo  ==========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python not found. Install from https://python.org
    pause & exit /b 1
)

:: Install deps if needed
if not exist ".deps_installed" (
    echo  Installing dependencies...
    pip install -r requirements.txt
    echo. > .deps_installed
    echo  Done.
    echo.
)

:: Check Ollama
where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo  WARNING: Ollama not found.
    echo  Install from https://ollama.com for local AI.
    echo  Or set API keys in backend\.env for cloud providers.
    echo.
)

echo  Starting backend...
echo  Keep this window open while using Lyze.
echo  Press Ctrl+C to stop.
echo.
python main.py
pause

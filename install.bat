@echo off
title 591 Scraper - Installing...

cd /d "%~dp0"

echo.
echo ============================================
echo      591 Scraper -- Installation
echo ============================================
echo.
echo This script will:
echo   1. Check Python environment
echo   2. Create virtual environment (.venv)
echo   3. Install requirements
echo   4. Install browser (Chromium)
echo.
echo Press any key to continue...
pause > nul

echo [1/4] Checking Python environment...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python not found!
    echo Please install Python and check "Add Python to PATH".
    pause
    exit /b 1
)
echo [+] Python found.

echo [2/4] Creating virtual environment (.venv)...
if not exist .venv\Scripts\python.exe (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [!] ERROR: Failed to create .venv!
        pause
        exit /b 1
    )
)
echo [+] Virtual environment ready.

echo [3/4] Installing requirements...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to install requirements!
    pause
    exit /b 1
)
echo [+] Requirements installed.

echo [4/4] Installing browser...
.venv\Scripts\playwright install chromium
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to install browser!
    pause
    exit /b 1
)
echo [+] Browser installed.

echo.
echo ============================================
echo       Installation Completed!
echo ============================================
echo.
echo Now you can run: run_scraper.bat
echo.
pause

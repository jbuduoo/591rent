@echo off
title 591 Scraper - Running...

cd /d "%~dp0"

echo.
echo ============================================
echo       591 Scraper -- Starting
echo ============================================
echo.

if not exist .venv\Scripts\python.exe (
    echo [!] ERROR: Virtual environment not found!
    echo Please run "install.bat" first.
    pause
    exit /b 1
)

echo Sequence:
echo   Step 1 / 4  Fetching Rent URLs (1_rent.py)
echo   Step 2 / 4  Extracting Rent Details (2_rent.py)
echo   Step 3 / 4  Fetching Sale URLs (3_sale.py)
echo   Step 4 / 4  Extracting Sale Details (4_sale.py)
echo.
echo Note:
echo   - Do not close this window while running.
echo   - Close Excel files before continuing.
echo.
echo Press any key to start...
pause > nul
echo.

.venv\Scripts\python run_all.py

if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo   [!] Execution failed with error.
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   [OK] All tasks completed!
    echo        Data updated to Google Sheets / Excel.
    echo ============================================
)
echo.
pause

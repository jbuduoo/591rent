@echo off
chcp 65001 > nul
title 591 爬蟲工具 - 首次安裝程式

:: 切換到此 .bat 檔案所在的目錄
cd /d "%~dp0"

echo.
echo  ============================================
echo       591 爬蟲工具 -- 首次安裝程式
echo  ============================================
echo.
echo  本程式將自動完成以下 4 個步驟：
echo  [1] 確認 Python 環境
echo  [2] 建立獨立執行環境
echo  [3] 安裝必要套件
echo  [4] 下載自動化瀏覽器（約 200MB）
echo.
echo  ⚠️  請確認電腦已連接網路，再按任意鍵繼續！
pause > nul
echo.

:: ──────────────────────────────────────────────
:: 步驟 1：確認 Python 已安裝
:: ──────────────────────────────────────────────
echo [1/4] 正在確認 Python 環境...

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ❌ 錯誤：找不到 Python！
    echo.
    echo  ▶ 請依照以下步驟安裝 Python：
    echo    1. 即將自動開啟 Python 下載頁面
    echo    2. 點擊頁面上的大按鈕「Download Python 3.x.x」
    echo    3. 執行下載的安裝程式
    echo    4. 安裝時，請務必勾選「Add Python to PATH」選項
    echo    5. 安裝完成後，重新執行本程式
    echo.
    start https://www.python.org/downloads/
    echo  （Python 下載頁面已在瀏覽器中開啟）
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo  ✅ 確認完成！已偵測到 %PY_VER%
echo.

:: ──────────────────────────────────────────────
:: 步驟 2：建立獨立執行環境 (.venv)
:: ──────────────────────────────────────────────
echo [2/4] 正在建立獨立執行環境...

if exist .venv\Scripts\python.exe (
    echo  ✅ 獨立環境已存在，跳過此步驟。
) else (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo.
        echo  ❌ 錯誤：建立環境失敗！
        echo  請通知技術人員協助處理。
        pause
        exit /b 1
    )
    echo  ✅ 獨立環境建立完成！
)
echo.

:: ──────────────────────────────────────────────
:: 步驟 3：安裝必要套件
:: ──────────────────────────────────────────────
echo [3/4] 正在安裝必要套件（可能需要 1~3 分鐘）...

.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo  ❌ 錯誤：套件安裝失敗！
    echo  請確認電腦已連接網路，再重新執行本程式。
    pause
    exit /b 1
)
echo  ✅ 套件安裝完成！
echo.

:: ──────────────────────────────────────────────
:: 步驟 4：下載 Playwright 自動化瀏覽器 (Chromium)
:: ──────────────────────────────────────────────
echo [4/4] 正在下載自動化瀏覽器（檔案約 200MB，請耐心等候）...
echo  （下載速度取決於網路狀況，通常需要 3~10 分鐘）

.venv\Scripts\playwright install chromium
if %errorlevel% neq 0 (
    echo.
    echo  ❌ 錯誤：瀏覽器下載失敗！
    echo  請確認電腦已連接網路，再重新執行本程式。
    pause
    exit /b 1
)
echo  ✅ 瀏覽器下載完成！
echo.

:: ──────────────────────────────────────────────
:: 安裝完成
:: ──────────────────────────────────────────────
echo.
echo  ============================================
echo        🎉 安裝全部完成！
echo  ============================================
echo.
echo  日後執行爬蟲，只需雙擊：
echo  ▶ 執行爬蟲.bat
echo.
echo  本視窗可以關閉了。
echo.
pause

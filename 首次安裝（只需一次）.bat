@echo off
chcp 65001 > nul
title 591 爬蟲工具 - 首次安裝程式

:: 切換到此 .bat 檔案所在的目錄
cd /d "%~dp0"

echo.
echo ============================================
echo      591 爬蟲工具 -- 首次安裝程式
echo ============================================
echo.
echo 本程式將自動完成以下步驟：
echo   1. 確認 Python 環境
echo   2. 建立獨立執行環境 (.venv)
echo   3. 安裝必要套件
echo   4. 下載自動化瀏覽器
echo.
echo 請按任意鍵繼續...
pause > nul

:: 步驟 1：確認 Python
echo [1/4] 正在確認 Python 環境...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 錯誤：找不到 Python！
    echo 請安裝 Python 並勾選「Add Python to PATH」。
    pause
    exit /b 1
)
echo [+] Python 已安裝。

:: 步驟 2：建立環境
echo [2/4] 正在建立獨立執行環境...
if not exist .venv\Scripts\python.exe (
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [!] 錯誤：建立環境失敗！
        pause
        exit /b 1
    )
)
echo [+] 獨立環境建立完成。

:: 步驟 3：安裝套件
echo [3/4] 正在安裝必要套件...
.venv\Scripts\pip install --upgrade pip --quiet
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] 錯誤：套件安裝失敗！
    pause
    exit /b 1
)
echo [+] 套件安裝完成。

:: 步驟 4：下載瀏覽器
echo [4/4] 正在下載自動化瀏覽器...
.venv\Scripts\playwright install chromium
if %errorlevel% neq 0 (
    echo [!] 錯誤：瀏覽器下載失敗！
    pause
    exit /b 1
)
echo [+] 瀏覽器下載完成。

echo.
echo ============================================
echo       安裝全部完成！
echo ============================================
echo.
echo 您現在可以執行「執行爬蟲.bat」了。
echo.
pause

@echo off
chcp 65001 > nul
title 591 爬蟲工具 - 執行中...

:: 切換到此 .bat 檔案所在的目錄
cd /d "%~dp0"

echo.
echo ============================================
echo       591 爬蟲工具 -- 開始執行
echo ============================================
echo.

:: 確認環境已安裝
if not exist .venv\Scripts\python.exe (
    echo [!] 錯誤：找不到執行環境！
    echo.
    echo 請先執行「首次安裝（只需一次）.bat」
    echo 安裝完成後，再執行本程式。
    echo.
    pause
    exit /b 1
)

echo 執行順序：
echo   步驟 1 / 4  租屋網址蒐集 (1_rent.py)
echo   步驟 2 / 4  租屋詳細資訊 (2_rent.py)
echo   步驟 3 / 4  售屋網址蒐集 (3_sale.py)
echo   步驟 4 / 4  售屋詳細資訊 (4_sale.py)
echo.
echo 注意：
echo   - 執行期間請勿關閉此視窗
echo   - 若 Excel 檔案已開啟，請先關閉
echo.
echo 按任意鍵開始...
pause > nul
echo.

:: 執行主程式
.venv\Scripts\python run_all.py

:: 顯示結束狀態
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo   [!] 執行過程中發生錯誤
    echo ============================================
) else (
    echo.
    echo ============================================
    echo   [OK] 所有任務完成！
    echo        資料已更新至 Excel 檔案。
    echo ============================================
)
echo.
pause

@echo off
chcp 65001 >nul
title HWOOD - Tự Động Đồng Bộ Code Lên GitHub
echo ==============================================================
echo        HWOOD - DONG BO CODE LEN GITHUB CHO STREAMLIT CLOUD
echo ==============================================================
echo.

cd /d "%~dp0"

"C:\Users\HOME CENTER GROUP\AppData\Local\Programs\Python\Python312\python.exe" modules\github_sync.py

echo.
echo ==============================================================
echo   DA HOAN TAT DONG BO! STREAMLIT CLOUD SE TU DONG CAP NHAT.
echo ==============================================================
pause

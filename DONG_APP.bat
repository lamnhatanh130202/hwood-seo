@echo off
title DONG UNG DUNG HWOOD SEO AI
cd /d "%~dp0"

echo Dang tat ung dung HWOOD SEO AI...
powershell -NoProfile -Command "Get-Process -Name python,pythonw -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*streamlit*' } | Stop-Process -Force"
echo.
echo [OK] Da dong tat ca tien trinh ung dung HWOOD SEO AI thanh cong.
timeout /t 2 >nul

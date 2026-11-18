@echo off
title TAO ICON HWOOD SEO AI
cd /d "%~dp0"

echo ===================================================
echo   TAO PHIM TAT UNG DUNG HWOOD SEO AI LEN DESKTOP
echo ===================================================
echo.

python cai_dat_shortcut.py 2>nul
if %errorlevel% neq 0 (
    py -3 cai_dat_shortcut.py 2>nul
    if %errorlevel% neq 0 (
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" cai_dat_shortcut.py
    )
)

echo.
pause

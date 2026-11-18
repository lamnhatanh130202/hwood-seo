@echo off
title CAI DAT HWOOD SEO ASSISTANT
cd /d "%~dp0"

echo ===================================================
echo   CAI DAT MOI TRUONG CHO HWOOD SEO ASSISTANT
echo ===================================================
echo.

set "PY="

python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python"
    goto :INSTALL
)

py -3 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=py"
    goto :INSTALL
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :INSTALL
    )
)

for /d %%D in ("C:\Program Files\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :INSTALL
    )
)

for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :INSTALL
    )
)

echo [LOI] Khong tim thay Python tren may tinh nay!
echo Ban hay tai va cai dat Python tai: https://www.python.org/downloads/
echo QUAN TRONG: Nho tich chon vao o [Add python.exe to PATH] khi cai dat!
echo.
pause
exit /b 1

:INSTALL
echo [1/3] Tim thay Python: %PY%
echo [2/3] Dang cai dat cac thu vien can thiet tu requirements.txt...

if "%PY%"=="python" (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo.
    echo [3/3] Dang cai dat Chromium cho Bot Playwright...
    python -m playwright install chromium
    echo [4/4] Dang tao shortcut Ung dung Desktop...
    python cai_dat_shortcut.py
) else if "%PY%"=="py" (
    py -3 -m pip install --upgrade pip
    py -3 -m pip install -r requirements.txt
    echo.
    echo [3/3] Dang cai dat Chromium cho Bot Playwright...
    py -3 -m playwright install chromium
    echo [4/4] Dang tao shortcut Ung dung Desktop...
    py -3 cai_dat_shortcut.py
) else (
    "%PY%" -m pip install --upgrade pip
    "%PY%" -m pip install -r requirements.txt
    echo.
    echo [3/3] Dang cai dat Chromium cho Bot Playwright...
    "%PY%" -m playwright install chromium
    echo [4/4] Dang tao shortcut Ung dung Desktop...
    "%PY%" cai_dat_shortcut.py
)

echo.
echo ===================================================
echo   CAI DAT HOAN TAT!
echo   Icon "HWOOD SEO AI" da duoc tao tren Desktop.
echo   Ban co the nhap dup chuot de chay truc tiep nhu mot App.
echo ===================================================
echo.
pause

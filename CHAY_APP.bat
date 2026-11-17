@echo off
title HWOOD SEO ASSISTANT
cd /d "%~dp0"

echo ===================================================
echo   HWOOD SEO ASSISTANT - HE THONG TOI UU SEO
echo ===================================================
echo.

set "PY="

python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python"
    goto :RUN
)

py -3 -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=py"
    goto :RUN
)

for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :RUN
    )
)

for /d %%D in ("C:\Program Files\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :RUN
    )
)

for /d %%D in ("C:\Python3*") do (
    if exist "%%D\python.exe" (
        set "PY=%%D\python.exe"
        goto :RUN
    )
)

echo [LOI] Khong tim thay Python tren may tinh nay!
echo Vui long tai va cai dat Python tai: https://www.python.org/downloads/
echo Luu y: Nho tich chon vao o [Add python.exe to PATH] khi cai dat.
echo.
pause
exit /b 1

:RUN
if "%PY%"=="python" (
    python chay_app.py
) else if "%PY%"=="py" (
    py -3 chay_app.py
) else (
    "%PY%" chay_app.py
)

if errorlevel 1 (
    echo.
    echo [LOI] Co loi xay ra khi khoi dong.
    echo Vui long chay file CAI_DAT_LAN_DAU.bat de kiem tra hoac xem thong bao loi o tren.
    echo.
    pause
)

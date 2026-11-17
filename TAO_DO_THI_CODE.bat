@echo off
title GRAPHIFY - TAO DO THI TRI THUC CODEBASE
cd /d "%~dp0"

echo ===================================================
echo   GRAPHIFY - XAY DUNG DO THI TRI THUC CODEBASE
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
pause
exit /b 1

:RUN
if "%PY%"=="python" (
    python scripts/graphify_engine.py
) else if "%PY%"=="py" (
    py -3 scripts/graphify_engine.py
) else (
    "%PY%" scripts/graphify_engine.py
)

echo.
echo [HOAN TAT] Do thi da duoc tao trong thu muc: graphify-out\
echo Ban co the mo file: graphify-out\graph.html tren trinh duyet de xem so do truc quan!
echo.
pause

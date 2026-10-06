@echo off
title Grocery Billing App Runner
cd /d "%~dp0"

echo =======================================================
echo          Grocery Billing Web App (Windows)
echo =======================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

echo [1/3] Checking and applying database migrations...
".venv\Scripts\python.exe" manage.py migrate --noinput
echo.

echo [2/3] Starting Model Vision Service on port 8001...
start "Model Vision Service (Port 8001)" cmd /k "cd /d "%~dp0" && .venv\Scripts\uvicorn.exe model_service.main:app --host 0.0.0.0 --port 8001"
echo.

echo [3/3] Getting your local IP for phone camera access...
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0.*0.0.0.0') do (
    set LOCAL_IP=%%a
    goto :ip_found
)
:ip_found
echo.
echo =======================================================
echo App is starting!
echo.
echo PC Browser:    http://localhost:8000
echo Phone Browser: http://%LOCAL_IP%:8000
echo.
echo Default Admin:
echo   Username: admin
echo   Password: admin123
echo =======================================================
echo.
echo Starting Django Web Server (Press Ctrl+C to stop)...
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000

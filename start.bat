@echo off
chcp 65001 >nul
setlocal

::==============================================================================
:: Hardware Benchmark System - Start Script
::==============================================================================

echo.
echo =============================================================
echo   Hardware Benchmark System - Starting...
echo =============================================================
echo.

:: Get script directory
set SCRIPT_DIR=%~dp0

::==============================================================================
:: Start Backend
::==============================================================================
echo [1/2] Starting backend service...
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

start "Backend - Hardware Benchmark" cmd /k "cd /d "%SCRIPT_DIR%backend" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

::==============================================================================
:: Start Frontend
::==============================================================================
echo [2/2] Starting frontend service...
echo Frontend: http://localhost:5173
echo.

start "Frontend - Hardware Benchmark" cmd /k "cd /d "%SCRIPT_DIR%frontend" && npm run dev"

:: Wait for frontend
echo.
echo Waiting for frontend to start...
timeout /t 8 /nobreak >nul

::==============================================================================
:: Done
::==============================================================================
echo.
echo =============================================================
echo   Start Complete!
echo =============================================================
echo.
echo Access URLs:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API:      http://localhost:8000/docs
echo.
echo Login:
echo   Username: admin
echo   Password: admin123
echo.
echo =============================================================

:: Auto open browser
echo Opening browser...
start http://localhost:5173

echo.
pause

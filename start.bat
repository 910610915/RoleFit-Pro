@echo off
chcp 65001 >nul
setlocal

::==============================================================================
:: RoleFit Pro - Start Script
::==============================================================================

echo.
echo =============================================================
echo   RoleFit Pro - Starting...
echo =============================================================
echo.

:: Get script directory
set SCRIPT_DIR=%~dp0

::==============================================================================
:: Start Backend
::==============================================================================
echo [1/2] Starting backend service...
echo Backend: http://localhost:8000
echo.

cd /d "%SCRIPT_DIR%backend"
start "Backend - RoleFit Pro" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

::==============================================================================
:: Start Frontend
::==============================================================================
echo [2/2] Starting frontend service...
echo Frontend: http://localhost:5173
echo.

cd /d "%SCRIPT_DIR%frontend"
start "Frontend - RoleFit Pro" cmd /k "npm run dev"

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
start http://localhost:5173

echo.
pause

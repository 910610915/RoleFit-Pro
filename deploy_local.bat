@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

::==============================================================================
:: Hardware Benchmark System - Local Deploy Script (No Docker)
::==============================================================================

echo.
echo =============================================================
echo   Hardware Benchmark System - Local Deploy
echo   (No Docker, using SQLite database)
echo =============================================================
echo.

:: Record current directory
set PROJECT_DIR=%~dp0
echo [INFO] Project directory: %PROJECT_DIR%
echo.

::==============================================================================
:: Step 1: Check Python
::==============================================================================
echo [Step 1/6] Checking Python...
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+: https://www.python.org/downloads/
    echo Make sure Python is in your system PATH
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python is installed
echo.

::==============================================================================
:: Step 2: Check Node.js
::==============================================================================
echo [Step 2/6] Checking Node.js...
echo.

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js 18+: https://nodejs.org/
    echo Make sure Node.js is in your system PATH
    echo.
    pause
    exit /b 1
)

node --version
npm --version
echo [OK] Node.js is installed
echo.

::==============================================================================
:: Step 3: Install Backend Dependencies
::==============================================================================
echo [Step 3/6] Installing backend dependencies...
echo.

set BACKEND_DIR=%PROJECT_DIR%backend
echo [INFO] Entering: %BACKEND_DIR%
cd /d "%BACKEND_DIR%" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Cannot access backend directory: %BACKEND_DIR%
    pause
    exit /b 1
)

echo.
echo [INFO] Current directory: %CD%
echo.

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

if %errorlevel% neq 0 (
    echo [ERROR] pip upgrade failed
    pause
    exit /b 1
)

echo.
echo [INFO] Installing Python packages from requirements.txt...
echo.

python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install Python dependencies
    pause
    exit /b 1
)

echo [OK] Backend dependencies installed
echo.

::==============================================================================
:: Step 4: Configure Environment
::==============================================================================
echo [Step 4/6] Configuring environment variables...
echo.

cd /d "%BACKEND_DIR%"
if not exist ".env" (
    if exist ".env.sqlite" (
        copy ".env.sqlite" ".env"
        echo [OK] Created .env config file
    ) else (
        echo [WARNING] .env.sqlite not found, skipping
    )
) else (
    echo [INFO] .env already exists, skipping
)

echo.
echo [INFO] Initializing SQLite database...
echo.

python init_sqlite.py

if %errorlevel% neq 0 (
    echo [WARNING] Database init has errors, but continuing...
) else (
    echo [OK] Database initialized
)

echo.
echo [INFO] Adding test data...
echo.

python add_test_data.py

if %errorlevel% neq 0 (
    echo [WARNING] Test data script has errors, but continuing...
) else (
    echo [OK] Test data added
)

python add_more_results.py

if %errorlevel% neq 0 (
    echo [WARNING] Additional results script has errors, but continuing...
) else (
    echo [OK] Historical data added
)

echo.

::==============================================================================
:: Step 5: Install Frontend Dependencies
::==============================================================================
echo [Step 5/6] Installing frontend dependencies...
echo.

set FRONTEND_DIR=%PROJECT_DIR%frontend
cd /d "%FRONTEND_DIR%" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Cannot access frontend directory: %FRONTEND_DIR%
    pause
    exit /b 1
)

echo [INFO] Current directory: %CD%
echo.
echo [INFO] Installing Node.js packages...
echo.

call npm install

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo [OK] Frontend dependencies installed
echo.

::==============================================================================
:: Step 6: Start Services
::==============================================================================
echo [Step 6/6] Starting services...
echo.

:: Start backend
echo =============================================================
echo Starting backend service...
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo =============================================================

start "Backend - Hardware Benchmark" cmd /k "cd /d "%BACKEND_DIR%" && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [INFO] Waiting for backend to start (5 seconds)...
timeout /t 5 /nobreak >nul

:: Start frontend
echo.
echo =============================================================
echo Starting frontend service...
echo Frontend: http://localhost:5173
echo =============================================================

start "Frontend - Hardware Benchmark" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo [INFO] Waiting for frontend to start (8 seconds)...
timeout /t 8 /nobreak >nul

::==============================================================================
:: Done
::==============================================================================
echo.
echo =============================================================
echo   Deploy Complete!
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
echo.
echo Opening browser...
start http://localhost:5173
echo.
pause

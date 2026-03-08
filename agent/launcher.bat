@echo off
setlocal

title Hardware Benchmark Agent

echo ==========================================
echo   Hardware Benchmark Agent Launcher
echo ==========================================
echo.

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python: https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [OK] Node.js:
node --version
echo [OK] Python:
python --version
echo.

:: Check Node.js dependencies
if not exist "%~dp0nodejs\hardware_info\node_modules" (
    echo [INFO] Installing Node.js dependencies...
    cd /d "%~dp0nodejs\hardware_info"
    call npm install
    cd /d "%~dp0"
    if errorlevel 1 (
        echo [ERROR] Node.js dependencies install failed!
        pause
        exit /b 1
    )
)
echo [OK] Node.js dependencies installed
echo.

echo Select mode:
echo   1. Start Agent (device registration + heartbeat + monitor)
echo   2. Exit
echo.

set /p choice="Enter option (1/2): "

if "%choice%"=="1" (
    echo.
    echo Starting Hardware Agent...
    python "%~dp0hardware_agent.py" --server http://localhost:8000
    echo.
    echo Agent exited.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

if "%choice%"=="2" (
    exit /b 0
)

echo Invalid option, press any key to exit...
pause >nul

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
echo   1. Start Agent (device registration + heartbeat)
echo   2. Start Monitor (real-time metrics)
echo   3. Start Both (recommended)
echo   4. Exit
echo.

set /p choice="Enter option (1/2/3/4): "

if "%choice%"=="1" (
    echo.
    echo Starting Hardware Agent...
    python "%~dp0hardware_agent.py" --server http://localhost:8000
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo Starting Hardware Monitor...
    python "%~dp0hardware_monitor.py"
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

if "%choice%"=="3" (
    echo.
    echo Starting Agent + Monitor (dual window mode)
    echo Server: http://localhost:8000
    echo.
    echo [Window 1] Hardware Agent
    echo [Window 2] Hardware Monitor
    echo.
    start "Hardware Monitor" cmd /k "cd /d "%~dp0" && python hardware_monitor.py"
    python "%~dp0hardware_agent.py" --server http://localhost:8000
    exit /b 0
)

if "%choice%"=="4" (
    exit /b 0
)

echo Invalid option, press any key to exit...
pause >nul

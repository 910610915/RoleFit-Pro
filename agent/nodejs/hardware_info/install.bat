@echo off
chcp 65001 >nul 2>&1

echo ==========================================
echo   Installing Node.js Dependencies
echo ==========================================
echo.

cd /d "%~dp0hardware_info"

:: Check if node is available
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Show node version
node --version
echo.

:: Install dependencies
echo Installing systeminformation...
call npm install

echo.
echo Installation complete!
echo.
pause

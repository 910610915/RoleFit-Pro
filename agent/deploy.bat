@echo off
setlocal

title RoleFit Pro - Deploy Tool

echo ==========================================
echo   RoleFit Pro - Deploy Tool
echo   Hardware Monitoring Client
echo ==========================================
echo.

set "SCRIPT_DIR=%~dp0"

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Python not found!
    echo   Please install Python: https://www.python.org/
    echo.
    pause
    exit /b 1
)
python --version
echo   [OK] Python installed

echo.
echo [2/5] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [ERROR] Node.js not found!
    echo   Please install Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
node --version
echo   [OK] Node.js installed

echo.
echo [3/5] Installing Python dependencies...
cd /d "%SCRIPT_DIR%"
python -m pip install --upgrade pip -q
python -m pip install requests -q
echo   [OK] Python dependencies installed

echo.
echo [4/5] Installing Node.js dependencies...
cd /d "%SCRIPT_DIR%\nodejs\hardware_info"
call npm install
if errorlevel 1 (
    echo   [ERROR] npm install failed!
    pause
    exit /b 1
)
echo   [OK] Node.js dependencies installed

echo.
echo [5/5] Creating desktop shortcut...

set "DESKTOP=%USERPROFILE%\Desktop"

echo @echo off > "%DESKTOP%\RoleFit Pro Start.bat"
echo cd /d "%SCRIPT_DIR%" >> "%DESKTOP%\RoleFit Pro Start.bat"
echo call launcher.bat >> "%DESKTOP%\RoleFit Pro Start.bat"

echo   [OK] Desktop shortcut created

echo.
echo ==========================================
echo   Deploy Complete!
echo ==========================================
echo.
echo Press any key to start...
pause >nul

cd /d "%SCRIPT_DIR%"
call launcher.bat

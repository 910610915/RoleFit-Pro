@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title Hardware Benchmark Agent

echo ==========================================
echo   Hardware Benchmark Agent Launcher
echo ==========================================
echo.
echo Select mode:
echo   1. Hardware Monitor (continuous)
echo   2. Script Executor (one-time)
echo   3. Exit
echo.

set /p choice="Enter option (1/2/3): "

if "%choice%"=="1" (
    echo.
    echo Starting Hardware Monitor...
    "C:\Program Files\Python39\python.exe" "%~dp0hardware_agent.py" --server http://localhost:8000
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo Starting Script Executor...
    "C:\Program Files\Python39\python.exe" "%~dp0script_executor.py" --server http://localhost:8000
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
)

if "%choice%"=="3" (
    exit /b 0
)

echo Invalid option, press any key to exit...
pause >nul

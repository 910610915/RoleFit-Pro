@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title Hardware Benchmark Agent

echo ==========================================
echo   Hardware Benchmark Agent Launcher
echo ==========================================
echo.

:: 检查 Node.js 是否安装
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] Node.js 未安装!
    echo 请先安装 Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: 自动检测 Python 路径
set PYTHON=
for %%p in (python python3 python3.11 python3.10 python3.9 python3.8) do (
    if not defined PYTHON (
        where %%p >nul 2>&1 && set PYTHON=%%p
    )
)

if not defined PYTHON (
    echo [错误] Python 未安装!
    echo 请先安装 Python 3.8+: https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo [✓] Node.js: 
node --version
echo [✓] Python: 
%PYTHON% --version
echo.

:: 检查 Node.js 依赖是否安装
if not exist "%~dp0nodejs\hardware_info\node_modules" (
    echo [提示] 正在安装 Node.js 依赖...
    cd /d "%~dp0nodejs\hardware_info"
    call npm install
    cd /d "%~dp0"
    if %ERRORLEVEL% NEQ 0 (
        echo [错误] Node.js 依赖安装失败!
        pause
        exit /b 1
    )
)
echo [✓] Node.js 依赖已安装
echo.

echo 选择运行模式:
echo   1. 启动 Agent (注册设备 + 心跳)
echo   2. 启动性能监控 (实时指标上报)
echo   3. 同时启动 (推荐)
echo   4. 退出
echo.

set /p choice="请输入选项 (1/2/3/4): "

if "%choice%"=="1" (
    echo.
    echo 正在启动 Hardware Agent...
    echo 服务器: http://localhost:8000
    %PYTHON% "%~dp0hardware_agent.py" --server http://localhost:8000
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 0
)

if "%choice%"=="2" (
    echo.
    echo 正在启动 Hardware Monitor...
    echo 服务器: http://localhost:8000
    %PYTHON% "%~dp0hardware_monitor.py"
    echo.
    echo 按任意键退出...
    pause >nul
    exit /b 0
)

if "%choice%"=="3" (
    echo.
    echo 启动 Agent + Monitor (双窗口模式)
    echo 服务器: http://localhost:8000
    echo.
    echo [窗口1] Hardware Agent - 设备注册和心跳
    echo [窗口2] Hardware Monitor - 实时性能监控
    echo.
    start "Hardware Monitor" cmd /k "cd /d "%~dp0" && %PYTHON% hardware_monitor.py"
    %PYTHON% "%~dp0hardware_agent.py" --server http://localhost:8000
    exit /b 0
)

if "%choice%"=="4" (
    exit /b 0
)

echo 无效选项，按任意键退出...
pause >nul

@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

title RoleFit Pro - 一键部署工具

echo ==========================================
echo   RoleFit Pro - 一键部署工具
echo   硬件监测与性能监控客户端
echo ==========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [提示] 建议以管理员身份运行以获得最佳体验
    echo.
)

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

:: 创建临时目录
if not exist "%TEMP%\RoleFit_Deploy" (
    mkdir "%TEMP%\RoleFit_Deploy"
)

echo [1/5] 检查 Python 环境...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   Python 未安装，正在下载安装...
    echo   (如需手动安装，请访问: https://www.python.org/downloads/)
    echo   安装时请勾选 "Add Python to PATH"
    echo.
    echo   按任意键打开 Python 下载页面...
    pause >nul
    start https://www.python.org/downloads/
    echo   请手动安装 Python 后重新运行此脚本
    pause
    exit /b 1
)

:: 检查 Python 版本
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo   [✓] %PYTHON_VERSION%

echo.
echo [2/5] 检查 Node.js 环境...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   Node.js 未安装，正在下载安装...
    echo   (如需手动安装，请访问: https://nodejs.org/)
    echo.
    echo   按任意键打开 Node.js 下载页面...
    pause >nul
    start https://nodejs.org/
    echo   请手动安装 Node.js 后重新运行此脚本
    pause
    exit /b 1
)

:: 检查 Node.js 版本
for /f "tokens=*" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo   [✓] Node.js %NODE_VERSION%

echo.
echo [3/5] 安装 Python 依赖...
cd /d "%SCRIPT_DIR%"
python -m pip install --upgrade pip >nul 2>&1
if exist requirements.txt (
    python -m pip install -r requirements.txt >nul 2>&1
) else (
    python -m pip install psutil requests wmi >nul 2>&1
)
echo   [✓] Python 依赖安装完成

echo.
echo [4/5] 安装 Node.js 依赖...
cd /d "%SCRIPT_DIR%\nodejs\hardware_info"
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo   [✗] Node.js 依赖安装失败
    pause
    exit /b 1
)
echo   [✓] Node.js 依赖安装完成

echo.
echo [5/5] 创建桌面快捷方式...

:: 创建启动脚本副本到桌面
set "DESKTOP=%USERPROFILE%\Desktop"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: 创建一键启动脚本
echo @echo off > "%DESKTOP%\RoleFit Pro 启动.bat"
echo cd /d "%SCRIPT_DIR%" >> "%DESKTOP%\RoleFit Pro 启动.bat"
echo call launcher.bat >> "%DESKTOP%\RoleFit Pro 启动.bat"

:: 添加到开机自启动
echo @echo off > "%STARTUP_FOLDER%\RoleFit Pro 启动.bat"
echo cd /d "%SCRIPT_DIR%" >> "%STARTUP_FOLDER%\RoleFit Pro 启动.bat"
echo start /min launcher.bat >> "%STARTUP_FOLDER%\RoleFit Pro 启动.bat"

echo   [✓] 桌面快捷方式已创建: "%DESKTOP%\RoleFit Pro 启动.bat"
echo   [✓] 已添加开机自启动

echo.
echo ==========================================
echo   部署完成!
echo ==========================================
echo.
echo 下一步:
echo   1. 双击桌面上的 "RoleFit Pro 启动.bat"
echo   2. 选择运行模式 (推荐选择 3)
echo   3. 确保服务器地址正确 (默认: http://localhost:8000)
echo.
echo 如需修改服务器地址，请编辑 launcher.bat
echo.
echo 按任意键启动程序...
pause >nul

:: 启动程序
cd /d "%SCRIPT_DIR%"
call launcher.bat

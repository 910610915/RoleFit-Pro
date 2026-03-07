@echo off
setlocal

title RoleFit Pro - 一键部署工具

echo ==========================================
echo   RoleFit Pro - 一键部署工具
echo   硬件监测与性能监控客户端
echo ==========================================
echo.

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"

echo [1/5] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] Python 未安装!
    echo   请先安装 Python: https://www.python.org/
    echo.
    pause
    exit /b 1
)
python --version
echo   [OK] Python 已安装

echo.
echo [2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] Node.js 未安装!
    echo   请先安装 Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)
node --version
echo   [OK] Node.js 已安装

echo.
echo [3/5] 安装 Python 依赖...
cd /d "%SCRIPT_DIR%"
python -m pip install --upgrade pip -q
python -m pip install requests -q
echo   [OK] Python 依赖安装完成

echo.
echo [4/5] 安装 Node.js 依赖...
cd /d "%SCRIPT_DIR%\nodejs\hardware_info"
call npm install
if errorlevel 1 (
    echo   [错误] npm install 失败!
    pause
    exit /b 1
)
echo   [OK] Node.js 依赖安装完成

echo.
echo [5/5] 创建桌面快捷方式...

set "DESKTOP=%USERPROFILE%\Desktop"

:: 创建启动脚本
echo @echo off > "%DESKTOP%\RoleFit Pro 启动.bat"
echo cd /d "%SCRIPT_DIR%" >> "%DESKTOP%\RoleFit Pro 启动.bat"
echo call launcher.bat >> "%DESKTOP%\RoleFit Pro 启动.bat"

echo   [OK] 桌面快捷方式已创建

echo.
echo ==========================================
echo   部署完成!
echo ==========================================
echo.
echo 按任意键启动程序...
pause >nul

:: 启动 launcher
cd /d "%SCRIPT_DIR%"
call launcher.bat

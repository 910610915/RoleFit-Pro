@echo off
chcp 65001 >nul
title RoleFit Pro 一键部署脚本

echo ========================================
echo   RoleFit Pro 一键部署脚本
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本
    echo.
)

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   未检测到 Python，正在尝试安装...
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    if %errorlevel% neq 0 (
        echo   [错误] Python 安装失败，请手动安装 Python 3.10+
        echo   下载地址: https://www.python.org/downloads/
        pause
        exit /b 1
    )
    :: 刷新环境变量
    set "PATH=C:\Program Files\Python312;C:\Program Files\Python312\Scripts;%PATH%"
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo   已安装: %PYTHON_VERSION%

echo.
echo [2/6] 安装后端依赖...
cd /d "%SCRIPT_DIR%backend"
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo   [错误] 依赖安装失败
    pause
    exit /b 1
)
echo   依赖安装完成

echo.
echo [3/6] 初始化数据库...
python init_sqlite.py >nul 2>&1
echo   数据库初始化完成

echo.
echo [4/6] 创建启动脚本...
echo @echo off > "%SCRIPT_DIR%start-backend.bat"
echo cd /d "%%~dp0backend" >> "%SCRIPT_DIR%start-backend.bat"
echo uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> "%SCRIPT_DIR%start-backend.bat"

echo   启动脚本已创建: start-backend.bat

echo.
echo [5/6] 启动后端服务...
start "RoleFit Pro Backend" cmd /k "cd /d "%SCRIPT_DIR%backend" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo ========================================
echo   部署完成！
echo ========================================
echo.
echo   后端地址: http://localhost:8000
echo   API 文档: http://localhost:8000/docs
echo.
echo   下一步：
echo   1. 在浏览器打开 http://localhost:5173 使用前端
echo   2. 或者部署前端后连接到此后端
echo.
pause

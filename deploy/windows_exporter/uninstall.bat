@echo off
REM windows_exporter 卸载脚本
REM 用于卸载 windows_exporter 服务

setlocal EnableDelayedExpansion

echo ============================================
echo   Windows Exporter 卸载脚本
echo ============================================
echo.

set "SERVICE_NAME=windows_exporter"

REM 检查管理员权限
echo [检查] 管理员权限...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo   [错误] 请以管理员身份运行此脚本！
    pause
    exit /b 1
)
echo   [OK]
echo.

REM 停止服务
echo [停止] 停止服务...
net stop %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] 服务已停止
) else (
    echo   [跳过] 服务未运行
)
echo.

REM 删除服务
echo [删除] 删除服务...
sc delete %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] 服务已删除
) else (
    echo   [跳过] 服务不存在
)
echo.

REM 删除安装目录（可选）
echo [清理] 是否删除安装目录?
echo   按 Y 确认删除，按其他键跳过...
set /p confirm=
if /i "%confirm%"=="Y" (
    if exist "C:\Program Files\windows_exporter" (
        rmdir /s /q "C:\Program Files\windows_exporter"
        echo   [OK] 安装目录已删除
    ) else (
        echo   [跳过] 目录不存在
    )
)
echo.

echo ============================================
echo   卸载完成
echo ============================================
pause
endlocal

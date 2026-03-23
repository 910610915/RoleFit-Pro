@echo off
REM windows_exporter 部署脚本
REM 用于在 Windows 机器上自动安装和配置 windows_exporter
REM 
REM 使用方式（管理员权限）:
REM   deploy.bat
REM
REM 卸载:
REM   uninstall.bat

setlocal EnableDelayedExpansion

echo ============================================
echo   Windows Exporter 部署脚本
echo   用于 Prometheus 监控系统
echo ============================================
echo.

REM ============================================
REM 配置
REM ============================================
set "EXPORTER_VERSION=0.28.1"
set "EXPORTER_URL=https://github.com/prometheus/windows_exporter/releases/download/v%EXPORTER_VERSION%/windows_exporter-%EXPORTER_VERSION%-amd64.exe"
set "INSTALL_DIR=C:\Program Files\windows_exporter"
set "EXPORTER_NAME=windows_exporter-%EXPORTER_VERSION%-amd64.exe"
set "SERVICE_NAME=windows_exporter"
set "PORT=9182"

REM 启用的采集器
set "ENABLED_COLLECTORS=cpu,cs,logical_disk,memory,net,thermalzone,gpu"

REM ============================================
REM 步骤 1: 检查管理员权限
REM ============================================
echo [步骤 1/6] 检查管理员权限...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo   [错误] 请以管理员身份运行此脚本！
    echo   右键 -> 以管理员身份运行
    echo.
    pause
    exit /b 1
)
echo   [OK] 管理员权限确认
echo.

REM ============================================
REM 步骤 2: 创建安装目录
REM ============================================
echo [步骤 2/6] 创建安装目录...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo   [OK] 目录已创建: %INSTALL_DIR%
) else (
    echo   [OK] 目录已存在: %INSTALL_DIR%
)
echo.

REM ============================================
REM 步骤 3: 下载 windows_exporter
REM ============================================
echo [步骤 3/6] 下载 windows_exporter v%EXPORTER_VERSION%...
if exist "%INSTALL_DIR%\windows_exporter.exe" (
    echo   [跳过] windows_exporter 已存在
) else (
    echo   下载地址: %EXPORTER_URL%
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%EXPORTER_URL%' -OutFile '%INSTALL_DIR%\%EXPORTER_NAME%'"
    if %errorLevel% neq 0 (
        echo   [错误] 下载失败！
        echo   请手动下载并放置到: %INSTALL_DIR%\%EXPORTER_NAME%
        echo.
        pause
        exit /b 1
    )
    echo   [OK] 下载完成
)
echo.

REM ============================================
REM 步骤 4: 安装为 Windows 服务
REM ============================================
echo [步骤 4/6] 安装为 Windows 服务...

REM 检查服务是否已存在
sc query %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo   [信息] 服务已存在，正在停止...
    net stop %SERVICE_NAME% >nul 2>&1
    sc delete %SERVICE_NAME% >nul 2>&1
    echo   [OK] 已删除旧服务
)

REM 复制可执行文件
copy "%INSTALL_DIR%\%EXPORTER_NAME%" "%INSTALL_DIR%\windows_exporter.exe" /Y >nul

REM 创建服务
echo   正在注册服务...
"%INSTALL_DIR%\windows_exporter.exe" --collectors.enabled=%ENABLED_COLLECTORS% --telemetry.addr=:%PORT% --service.install --service.name=%SERVICE_NAME%
if %errorLevel% neq 0 (
    echo   [错误] 服务安装失败！
    pause
    exit /b 1
)
echo   [OK] 服务已注册
echo.

REM ============================================
REM 步骤 5: 启动服务
REM ============================================
echo [步骤 5/6] 启动服务...
net start %SERVICE_NAME%
if %errorLevel% neq 0 (
    echo   [错误] 服务启动失败！
    echo   请检查事件查看器中的错误日志
    pause
    exit /b 1
)
echo   [OK] 服务已启动
echo.

REM ============================================
REM 步骤 6: 验证安装
REM ============================================
echo [步骤 6/6] 验证安装...
timeout /t 3 /nobreak >nul
curl -s http://localhost:%PORT%/metrics | findstr "windows_cpu" >nul
if %errorLevel% neq 0 (
    echo   [警告] 验证请求失败，但服务可能正在运行
) else (
    echo   [OK] 验证成功
)
echo.

REM ============================================
REM 完成
REM ============================================
echo ============================================
echo   部署完成！
echo ============================================
echo.
echo   服务信息:
echo     - 服务名称: %SERVICE_NAME%
echo     - 指标端口: http://localhost:%PORT%/metrics
echo     - 启用的采集器: %ENABLED_COLLECTORS%
echo.
echo   访问地址:
echo     - Prometheus 指标: http://localhost:%PORT%/metrics
echo.
echo   下一步:
echo     1. 在 Prometheus 服务器的 prometheus.yml 中添加此主机
echo     2. 在 Grafana 中导入 windows-exporter dashboard
echo.
echo   常用命令:
echo     - 查看服务状态: sc query %SERVICE_NAME%
echo     - 停止服务: net stop %SERVICE_NAME%
echo     - 卸载: uninstall.bat
echo.
echo ============================================

pause
endlocal

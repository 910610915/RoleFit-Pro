# RoleFit Pro 全自动安装脚本（前后端）
# 目标电脑只需运行这一条命令

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RoleFit Pro 全自动部署（前后端）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 安装 Git
Write-Host "[1/9] 检查 Git..." -ForegroundColor Yellow
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "  正在安装 Git（可能需要几分钟）..." -ForegroundColor Red
    winget install Git.Git --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 5
}

try {
    $gitVersion = git --version 2>&1
    Write-Host "  已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Git 安装失败，请手动安装 Git 后重试" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 2. 安装 Python
Write-Host ""
Write-Host "[2/9] 检查 Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "  正在安装 Python（可能需要几分钟）..." -ForegroundColor Red
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 10
}

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Python 安装失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 3. 安装 Node.js
Write-Host ""
Write-Host "[3/9] 检查 Node.js..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "  正在安装 Node.js..." -ForegroundColor Red
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 10
}

try {
    $nodeVersion = node --version 2>&1
    Write-Host "  已安装: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Node.js 安装失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 4. 刷新环境变量
Write-Host ""
Write-Host "[4/9] 刷新环境变量..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "  完成" -ForegroundColor Green

# 5. 克隆仓库
Write-Host ""
Write-Host "[5/9] 克隆代码仓库..." -ForegroundColor Yellow
$installDir = Join-Path $env:USERPROFILE "RoleFitPro"

if (Test-Path $installDir) {
    Write-Host "  代码已存在，更新中..." -ForegroundColor Yellow
    Set-Location $installDir
    git pull origin main 2>&1 | Out-Null
} else {
    Write-Host "  正在克隆（首次可能需要几分钟）..." -ForegroundColor Yellow
    git clone https://github.com/910610915/RoleFit-Pro.git $installDir 2>&1 | Out-Null
}

if (Test-Path $installDir) {
    Write-Host "  克隆完成: $installDir" -ForegroundColor Green
} else {
    Write-Host "  [错误] 克隆失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 6. 安装后端
Write-Host ""
Write-Host "[6/9] 安装后端依赖..." -ForegroundColor Yellow
Set-Location (Join-Path $installDir "backend")
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
pip install -r requirements.txt 2>&1 | Out-Null
Write-Host "  后端依赖安装完成" -ForegroundColor Green

# 7. 初始化数据库
Write-Host ""
Write-Host "[7/9] 初始化数据库..." -ForegroundColor Yellow
python init_sqlite.py 2>&1 | Out-Null
Write-Host "  数据库初始化完成" -ForegroundColor Green

# 8. 安装前端
Write-Host ""
Write-Host "[8/9] 安装前端依赖..." -ForegroundColor Yellow
Set-Location (Join-Path $installDir "frontend")
npm install 2>&1 | Out-Null
Write-Host "  前端依赖安装完成" -ForegroundColor Green

# 9. 启动服务
Write-Host ""
Write-Host "[9/9] 启动服务..." -ForegroundColor Yellow

# 创建启动脚本
$startScript = @"
@echo off
title RoleFit Pro 启动器
echo ========================================
echo   RoleFit Pro 启动中...
echo ========================================

echo.
echo [1] 启动后端服务...
start "RoleFit Pro Backend" cmd /k "cd /d "%~dp0backend" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2] 启动前端服务...
start "RoleFit Pro Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo   服务启动中，请稍候...
echo ========================================
echo.
echo 后端: http://localhost:8000
echo 前端: http://localhost:5173
echo.
echo 按任意键退出（服务会继续在后台运行）
pause >nul
"@

$startScript | Out-File -FilePath (Join-Path $installDir "start.bat") -Encoding UTF8

# 启动后端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# 启动前端
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  后端地址: http://localhost:8000" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  前端地址: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "  请在浏览器打开 http://localhost:5173" -ForegroundColor Cyan
Write-Host "  默认账号: admin / admin123" -ForegroundColor Cyan
Write-Host ""

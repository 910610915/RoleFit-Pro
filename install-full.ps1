# RoleFit Pro 全自动安装脚本
# 目标电脑只需运行这一条命令

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RoleFit Pro 全自动部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 安装 Git
Write-Host "[1/7] 检查 Git..." -ForegroundColor Yellow
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "  正在安装 Git..." -ForegroundColor Red
    winget install Git.Git --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 5
}

try {
    $gitVersion = git --version 2>&1
    Write-Host "  已安装: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  [错误] Git 安装失败，请手动安装 Git" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 2. 安装 Python
Write-Host ""
Write-Host "[2/7] 检查 Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "  正在安装 Python..." -ForegroundColor Red
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

# 3. 刷新环境变量
Write-Host ""
Write-Host "[3/7] 刷新环境变量..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "  完成" -ForegroundColor Green

# 4. 克隆仓库
Write-Host ""
Write-Host "[4/7] 克隆代码仓库..." -ForegroundColor Yellow
$installDir = Join-Path $env:USERPROFILE "RoleFitPro"

if (Test-Path $installDir) {
    Write-Host "  代码已存在，更新中..." -ForegroundColor Yellow
    Set-Location $installDir
    git pull origin main 2>&1 | Out-Null
} else {
    Write-Host "  正在克隆..." -ForegroundColor Yellow
    git clone https://github.com/910610915/RoleFit-Pro.git $installDir 2>&1 | Out-Null
}

if (Test-Path $installDir) {
    Write-Host "  克隆完成: $installDir" -ForegroundColor Green
} else {
    Write-Host "  [错误] 克隆失败" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 5. 安装后端依赖
Write-Host ""
Write-Host "[5/7] 安装后端依赖..." -ForegroundColor Yellow
Set-Location (Join-Path $installDir "backend")

# 升级 pip
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# 安装依赖
pip install -r requirements.txt 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [警告] 部分依赖安装可能有警告，请继续..." -ForegroundColor Yellow
}
Write-Host "  依赖安装完成" -ForegroundColor Green

# 6. 初始化数据库
Write-Host ""
Write-Host "[6/7] 初始化数据库..." -ForegroundColor Yellow
python init_sqlite.py 2>&1 | Out-Null
Write-Host "  数据库初始化完成" -ForegroundColor Green

# 7. 启动服务
Write-Host ""
Write-Host "[7/7] 启动后端服务..." -ForegroundColor Yellow
Write-Host "  启动中..." -ForegroundColor Yellow

# 创建启动脚本
$startScript = @"
@echo off
cd /d "%~dp0"
title RoleFit Pro 后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
"@

$startScript | Out-File -FilePath (Join-Path $installDir "start.bat") -Encoding UTF8

# 后台启动
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  后端地址: http://localhost:8000" -ForegroundColor White
Write-Host "  API 文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  前端地址: http://localhost:5173" -ForegroundColor White
Write-Host ""
Write-Host "  如需停止服务，请关闭命令行窗口" -ForegroundColor Cyan
Write-Host ""

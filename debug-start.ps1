# RoleFit Pro - Debug Start Script
$ErrorActionPreference = "Continue"

$installDir = Join-Path $env:USERPROFILE "RoleFitPro"
$backendDir = Join-Path $installDir "backend"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RoleFit Pro - Manual Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if directories exist
if (-not (Test-Path $backendDir)) {
    Write-Host "[错误] 代码目录不存在，请先运行一键安装脚本" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

Set-Location $backendDir

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[1/4] 创建 .env 文件..." -ForegroundColor Yellow
    $envContent = @"
APP_NAME=RoleFitPro
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./hardware_benchmark.db
DATABASE_URL_SYNC=sqlite:///./hardware_benchmark.db
SECRET_KEY=dev-secret-key-change-in-production-min-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=["*"]
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "  .env 创建完成" -ForegroundColor Green
} else {
    Write-Host "[1/4] .env 已存在" -ForegroundColor Green
}

# Check if database exists
$dbPath = Join-Path $backendDir "hardware_benchmark.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "[2/4] 初始化数据库..." -ForegroundColor Yellow
    python init_sqlite.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [错误] 数据库初始化失败" -ForegroundColor Red
    } else {
        Write-Host "  完成" -ForegroundColor Green
    }
} else {
    Write-Host "[2/4] 数据库已存在" -ForegroundColor Green
}

# Check dependencies
Write-Host "[3/4] 检查依赖..." -ForegroundColor Yellow
$required = @("fastapi", "uvicorn", "sqlalchemy", "pydantic")
foreach ($pkg in $required) {
    $installed = pip show $pkg 2>&1
    if ($installed -match "Name:") {
        Write-Host "  $pkg - OK" -ForegroundColor Green
    } else {
        Write-Host "  $pkg - 未安装，正在安装..." -ForegroundColor Red
        pip install $pkg --quiet
    }
}

# Start backend
Write-Host "[4/4] 启动后端服务..." -ForegroundColor Yellow
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  后端启动中，请查看下方错误信息..." -ForegroundColor Cyan
Write-Host "  如果看到 'Uvicorn running on' 表示成功" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run backend and show output
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

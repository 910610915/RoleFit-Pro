# RoleFit Pro - Simple Debug
$ErrorActionPreference = "Continue"

$installDir = Join-Path $env:USERPROFILE "RoleFitPro"
$backendDir = Join-Path $installDir "backend"

Write-Host "========================================"
Write-Host "  RoleFit Pro - Debug Start"
Write-Host "========================================"
Write-Host ""

if (-not (Test-Path $backendDir)) {
    Write-Host "ERROR: Code directory not found"
    exit 1
}

Set-Location $backendDir

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "[1/3] Creating .env file..."
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
    Write-Host "  .env created"
} else {
    Write-Host "[1/3] .env exists"
}

# Check database
$dbPath = Join-Path $backendDir "hardware_benchmark.db"
if (-not (Test-Path $dbPath)) {
    Write-Host "[2/3] Init database..."
    python init_sqlite.py
} else {
    Write-Host "[2/3] Database exists"
}

# Check deps
Write-Host "[3/3] Check dependencies..."
$deps = @("fastapi", "uvicorn", "sqlalchemy", "pydantic", "aiosqlite")
foreach ($d in $deps) {
    $check = pip show $d 2>&1
    if ($check -match "Name:") {
        Write-Host "  $d : OK"
    } else {
        Write-Host "  $d : MISSING - installing..."
        pip install $d --quiet
    }
}

Write-Host ""
Write-Host "========================================"
Write-Host "Starting backend..."
Write-Host "========================================"

# Start backend and show output
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

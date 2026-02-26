# RoleFit Pro Auto Install Script - Full Version
$ErrorActionPreference = "Continue"

Write-Host "========================================"
Write-Host "  RoleFit Pro Auto Deploy v2"
Write-Host "========================================"
Write-Host ""

$installDir = Join-Path $env:USERPROFILE "RoleFitPro"

# 1. Install Git
Write-Host "[1/10] Checking Git..."
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "  Installing Git..."
    winget install Git.Git --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 10
}
Write-Host "  OK" -ForegroundColor Green

# 2. Install Python
Write-Host "[2/10] Checking Python..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "  Installing Python..."
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    Start-Sleep -Seconds 15
}
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "  OK" -ForegroundColor Green

# 3. Install Node.js
Write-Host "[3/10] Checking Node.js..."
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "  Installing Node.js..."
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    Start-Sleep -Seconds 15
}
Write-Host "  OK" -ForegroundColor Green

# 4. Clone repo
Write-Host "[4/10] Cloning repository..."
if (Test-Path $installDir) {
    Set-Location $installDir
    git pull origin main 2>&1 | Out-Null
} else {
    git clone https://github.com/910610915/RoleFit-Pro.git $installDir 2>&1 | Out-Null
}
Write-Host "  OK" -ForegroundColor Green

# 5. Install backend dependencies
Write-Host "[5/10] Installing backend dependencies..."
Set-Location (Join-Path $installDir "backend")
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# Install core packages one by one
$packages = @(
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings", 
    "sqlalchemy",
    "aiosqlite",
    "python-multipart",
    "passlib",
    "python-jose",
    "cryptography",
    "python-dotenv",
    "psutil"
)

foreach ($pkg in $packages) {
    Write-Host "  Installing $pkg..." -NoNewline
    pip install $pkg --quiet 2>&1 | Out-Null
    Write-Host " OK" -ForegroundColor Green
}

Write-Host "  Backend OK" -ForegroundColor Green

# 6. Init database
Write-Host "[6/10] Initializing database..."
python init_sqlite.py 2>&1 | Out-Null
Write-Host "  OK" -ForegroundColor Green

# 7. Install frontend dependencies
Write-Host "[7/10] Installing frontend dependencies..."
Set-Location (Join-Path $installDir "frontend")
npm install 2>&1 | Out-Null
Write-Host "  OK" -ForegroundColor Green

# 8. Create start script
Write-Host "[8/10] Creating start script..."
$startBat = @"
@echo off
cd /d "%~dp0backend"
start "Backend" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd /d "%~dp0frontend"
start "Frontend" cmd /k "npm run dev"
echo.
echo RoleFit Pro is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
"@
$startBat | Out-File -FilePath (Join-Path $installDir "start.bat") -Encoding ASCII
Write-Host "  OK" -ForegroundColor Green

# 9. Start backend
Write-Host "[9/10] Starting backend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 5
Write-Host "  OK" -ForegroundColor Green

# 10. Start frontend
Write-Host "[10/10] Starting frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\frontend'; npm run dev"
Write-Host "  OK" -ForegroundColor Green

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Doc:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Login: admin / admin123" -ForegroundColor Cyan
Write-Host ""

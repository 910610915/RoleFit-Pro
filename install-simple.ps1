# RoleFit Pro Auto Install Script
$ErrorActionPreference = "Continue"

Write-Host "========================================"
Write-Host "  RoleFit Pro Auto Deploy"
Write-Host "========================================"
Write-Host ""

# 1. Install Git
Write-Host "[1/9] Checking Git..."
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host "  Installing Git..."
    winget install Git.Git --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 10
}
try { git --version 2>&1 | Out-Null; Write-Host "  Git installed" -ForegroundColor Green } catch { }

# 2. Install Python
Write-Host "[2/9] Checking Python..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "  Installing Python..."
    winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 15
}
try { python --version 2>&1 | Out-Null; Write-Host "  Python installed" -ForegroundColor Green } catch { }

# 3. Install Node.js
Write-Host "[3/9] Checking Node.js..."
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Host "  Installing Node.js..."
    winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements --silent
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    Start-Sleep -Seconds 15
}
try { node --version 2>&1 | Out-Null; Write-Host "  Node.js installed" -ForegroundColor Green } catch { }

# 4. Refresh PATH
Write-Host "[4/9] Refreshing environment..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 5. Clone repo
Write-Host "[5/9] Cloning repository..."
$installDir = Join-Path $env:USERPROFILE "RoleFitPro"

if (Test-Path $installDir) {
    Set-Location $installDir
    git pull origin main 2>&1 | Out-Null
} else {
    git clone https://github.com/910610915/RoleFit-Pro.git $installDir 2>&1 | Out-Null
}

if (Test-Path $installDir) {
    Write-Host "  Cloned successfully" -ForegroundColor Green
} else {
    Write-Host "  Clone failed! Please check network." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# 6. Install backend
Write-Host "[6/9] Installing backend..."
Set-Location (Join-Path $installDir "backend")
python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
pip install -r requirements.txt 2>&1 | Out-Null
Write-Host "  Backend installed" -ForegroundColor Green

# 7. Init database
Write-Host "[7/9] Initializing database..."
python init_sqlite.py 2>&1 | Out-Null
Write-Host "  Database ready" -ForegroundColor Green

# 8. Install frontend
Write-Host "[8/9] Installing frontend..."
Set-Location (Join-Path $installDir "frontend")
npm install 2>&1 | Out-Null
Write-Host "  Frontend installed" -ForegroundColor Green

# 9. Start services
Write-Host "[9/9] Starting services..."

$startBat = @"
@echo off
cd /d "%~dp0backend"
start "Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd /d "%~dp0frontend"
start "Frontend" cmd /k "npm run dev"
echo.
echo RoleFit Pro is starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
pause
"@

$startBat | Out-File -FilePath (Join-Path $installDir "start.bat") -Encoding ASCII

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\backend'; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend: http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Default login: admin / admin123" -ForegroundColor Cyan
Write-Host ""

# RoleFit Pro - Complete Reinstall Script
$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "  RoleFit Pro - Fresh Install"
Write-Host "========================================"

# Remove old directory completely
$installDir = Join-Path $env:USERPROFILE "RoleFitPro"
if (Test-Path $installDir) {
    Write-Host "Removing old installation..."
    Remove-Item -Recurse -Force $installDir
}

# Clone fresh
Write-Host "Cloning latest code..."
git clone https://github.com/910610915/RoleFit-Pro.git $installDir

# Go to backend
Set-Location (Join-Path $installDir "backend")

# Create .env file
Write-Host "Creating .env file..."
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

# Install deps
Write-Host "Installing Python packages..."
pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy aiosqlite python-multipart passlib python-jose cryptography python-dotenv psutil

# Init database
Write-Host "Initializing database..."
python init_sqlite.py

# Go to frontend
Set-Location (Join-Path $installDir "frontend")

# Install node modules
Write-Host "Installing frontend dependencies..."
npm install

# Start backend
Write-Host ""
Write-Host "========================================"
Write-Host "Starting backend..."
Write-Host "========================================"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 5

# Start frontend
Write-Host "Starting frontend..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$installDir\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================"
Write-Host "Done! Open http://localhost:5173"
Write-Host "Login: admin / admin123"
Write-Host "========================================"

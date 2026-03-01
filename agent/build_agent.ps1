# PyInstaller Build Script
Write-Host "=== Building RoleFit Pro Agent ===" -ForegroundColor Cyan

# 1. Check PyInstaller
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller packaging requests
}

# 2. Build
$agentDir = $PSScriptRoot
Set-Location $agentDir

# Clean previous build
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "*.spec") { Remove-Item "*.spec" -Force }

Write-Host "Starting build process..."
# Build command: Single file, Console mode (for debugging, change to --windowed for hidden), Include config
pyinstaller --noconfirm --onefile --console --name "RoleFitAgent" --clean --add-data "config.json;." hardware_agent.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild Successful!" -ForegroundColor Green
    Write-Host "Executable is located at: $(Join-Path $agentDir 'dist\RoleFitAgent.exe')"
    
    # Create a release zip (optional)
    # Compress-Archive -Path "dist\RoleFitAgent.exe", "config.json" -DestinationPath "RoleFitAgent_Release.zip" -Force
} else {
    Write-Host "`nBuild Failed!" -ForegroundColor Red
}

Pause
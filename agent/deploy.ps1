# RoleFit Pro Agent Deployment Script
# Run this script on the target Windows machine to set up the agent

Write-Host "=== RoleFit Pro Agent Deployment ===" -ForegroundColor Cyan

# 1. Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python command failed"
    }
} catch {
    Write-Host "Error: Python not found. Please install Python 3.8+ and add to PATH." -ForegroundColor Red
    Write-Host "Download: https://www.python.org/downloads/"
    exit 1
}

# 2. Create Virtual Environment
$venvPath = Join-Path $PSScriptRoot "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    python -m venv $venvPath
    if (-not (Test-Path $venvPath)) {
        Write-Host "Error: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Virtual environment already exists."
}

# 3. Install Dependencies
Write-Host "Installing dependencies..."
$pipPath = Join-Path $venvPath "Scripts\pip.exe"
& $pipPath install --upgrade pip
& $pipPath install -r (Join-Path $PSScriptRoot "requirements.txt")

# 4. Configuration
$configFile = Join-Path $PSScriptRoot "config.json"
$serverUrl = "http://localhost:8000"

if (Test-Path $configFile) {
    try {
        $config = Get-Content $configFile | ConvertFrom-Json
        if ($config.server_url) {
            $serverUrl = $config.server_url
        }
    } catch {
        Write-Host "Warning: Failed to read config.json" -ForegroundColor Yellow
    }
    Write-Host "Loaded config: Server URL = $serverUrl"
} else {
    $inputUrl = Read-Host "Enter Server URL (default: http://localhost:8000)"
    if ($inputUrl -ne "") {
        $serverUrl = $inputUrl
    }
    
    $config = @{
        server_url = $serverUrl
    }
    $config | ConvertTo-Json | Set-Content $configFile
    Write-Host "Saved config to $configFile"
}

# 5. Create Start Script
$startScript = Join-Path $PSScriptRoot "start_agent.bat"
$scriptContent = @"
@echo off
cd /d "%~dp0"
title RoleFit Pro Agent
echo Starting Agent...
echo Server: $serverUrl

if not exist venv (
    echo Virtual environment not found. Please run deploy.ps1 first.
    pause
    exit /b 1
)

venv\Scripts\python hardware_agent.py --server $serverUrl
if %errorlevel% neq 0 pause
"@

Set-Content $startScript $scriptContent
Write-Host "Created start script: $startScript" -ForegroundColor Green

Write-Host "`n=== Deployment Complete! ===" -ForegroundColor Cyan
Write-Host "1. Review config in config.json if needed"
Write-Host "2. Double-click 'start_agent.bat' to start the agent" -ForegroundColor Yellow

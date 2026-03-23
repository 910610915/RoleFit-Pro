# RoleFit Pro Prometheus Monitor - One-Click Setup
# No Docker required!
# Supports Windows paths with Chinese characters

param([switch]$Uninstall)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Use C:\Prometheus to avoid Chinese character issues in paths
$InstallRoot = "C:\Prometheus"
$InstallRootLocal = "$env:LOCALAPPDATA\RoleFitPrometheus"
$LogFile = "$InstallRoot\install.log"

function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8 -ErrorAction SilentlyContinue
    Write-Host $logMessage -ForegroundColor Cyan
}

if ($Uninstall) {
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  Uninstalling Prometheus Monitor" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""

    Write-Log "Stopping Prometheus..."
    $prometheusProc = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
    if ($prometheusProc) { Stop-Process -Name "prometheus" -Force -ErrorAction SilentlyContinue }
    
    Write-Log "Stopping Grafana..."
    $grafanaProc = Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue
    if ($grafanaProc) { Stop-Process -Name "grafana-server" -Force -ErrorAction SilentlyContinue }

    Write-Log "Stopping windows_exporter..."
    if (Get-Service -Name "winExporter" -ErrorAction SilentlyContinue) {
        Stop-Service -Name "winExporter" -Force -ErrorAction SilentlyContinue
        sc.exe delete winExporter -ErrorAction SilentlyContinue
    }
    $winExporterProc = Get-Process -Name "windows_exporter" -ErrorAction SilentlyContinue
    if ($winExporterProc) { Stop-Process -Name "windows_exporter" -Force -ErrorAction SilentlyContinue }

    Write-Log "Cleaning up..."
    if (Test-Path $InstallRoot) {
        Start-Sleep -Seconds 2
        Remove-Item -Path $InstallRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path $InstallRootLocal) {
        Remove-Item -Path $InstallRootLocal -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Uninstall Complete" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RoleFit Pro Prometheus Monitor Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Use LOCALAPPDATA for downloads to avoid permission issues
$DownloadRoot = "$env:LOCALAPPDATA\RoleFitPrometheus"
if (-not (Test-Path $DownloadRoot)) {
    New-Item -ItemType Directory -Path $DownloadRoot -Force | Out-Null
}
if (-not (Test-Path $InstallRoot)) {
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
}

Write-Log "Install directory: $InstallRoot"
Write-Log "Download cache: $DownloadRoot"
Write-Log "First run will download all dependencies..."

if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Log "Error: PowerShell 5.0+ required" "ERROR"
    exit 1
}

# 1. Install windows_exporter
Write-Host "" -ForegroundColor Yellow
Write-Host "[1/4] Installing windows_exporter..." -ForegroundColor Yellow

$winExporterPath = "$DownloadRoot\windows_exporter"
$winExporterExe = "$winExporterPath\windows_exporter.exe"
$winExporterUrl = "https://github.com/prometheus-community/windows_exporter/releases/download/v0.25.0/windows_exporter-0.25.0-amd64.exe"

if (-not (Test-Path $winExporterPath)) {
    New-Item -ItemType Directory -Path $winExporterPath -Force | Out-Null
}

if (-not (Test-Path $winExporterExe)) {
    Write-Log "Downloading windows_exporter..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $winExporterUrl -OutFile $winExporterExe -TimeoutSec 120 -UseBasicParsing
        Write-Log "windows_exporter downloaded"
    } catch {
        Write-Log "Download failed: $_" "ERROR"
        exit 1
    }
} else {
    Write-Log "windows_exporter already exists, skipping download"
}

$winExporterService = Get-Service -Name "winExporter" -ErrorAction SilentlyContinue
if (-not $winExporterService) {
    Write-Log "Registering windows_exporter service..."
    $installArgs = "--install --name winExporter --display-name `"Windows Exporter`" --description `"Prometheus Windows Exporter`" -- --collectors.enabled cpu,cs,logical_disk,memory,net,os,system,gpu,nvidia --web.listen-address :9182"
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $winExporterExe
    $psi.Arguments = $installArgs
    $psi.Verb = "RunAs"
    $psi.UseShellExecute = $true
    [System.Diagnostics.Process]::Start($psi) | Out-Null
}

$oldWinExporter = Get-Process -Name "windows_exporter" -ErrorAction SilentlyContinue
if ($oldWinExporter) {
    Stop-Process -Name "windows_exporter" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Log "Starting windows_exporter..."
$psi2 = New-Object System.Diagnostics.ProcessStartInfo
$psi2.FileName = $winExporterExe
$psi2.Arguments = "--collectors.enabled cpu,cs,logical_disk,memory,net,os,system,gpu,nvidia --web.listen-address :9182"
$psi2.UseShellExecute = $false
[System.Diagnostics.Process]::Start($psi2) | Out-Null
Start-Sleep -Seconds 2

$winExporterCheck = try { Invoke-WebRequest -Uri "http://localhost:9182/metrics" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($winExporterCheck) {
    Write-Log "windows_exporter started (http://localhost:9182/metrics)"
} else {
    Write-Log "windows_exporter may not have started properly" "WARN"
}

# 2. Install Prometheus
Write-Host "" -ForegroundColor Yellow
Write-Host "[2/4] Installing Prometheus..." -ForegroundColor Yellow

$prometheusPath = "$InstallRoot"
$prometheusExe = "$prometheusPath\prometheus.exe"
$prometheusConfigSrc = "$ScriptDir\deploy\prometheus\prometheus.yml"
$prometheusConfigDst = "$prometheusPath\prometheus.yml"
$prometheusUrl = "https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.windows-amd64.zip"

if (-not (Test-Path $prometheusPath)) {
    New-Item -ItemType Directory -Path $prometheusPath -Force | Out-Null
}

if (-not (Test-Path $prometheusExe)) {
    Write-Log "Downloading Prometheus..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $zipPath = "$DownloadRoot\prometheus-2.47.0.windows-amd64.zip"
        Invoke-WebRequest -Uri $prometheusUrl -OutFile $zipPath -TimeoutSec 300 -UseBasicParsing
        
        Write-Log "Extracting Prometheus..."
        Expand-Archive -Path $zipPath -DestinationPath $prometheusPath -Force
        
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        
        # Move contents from subfolder to root
        $extractedFolder = Get-ChildItem -Path $prometheusPath -Directory | Where-Object { $_.Name -like "prometheus*" } | Select-Object -First 1
        if ($extractedFolder -and $extractedFolder.Name -ne "") {
            Get-ChildItem -Path $extractedFolder.FullName | Move-Item -Destination $prometheusPath -Force -ErrorAction SilentlyContinue
            Remove-Item $extractedFolder.FullName -Force -ErrorAction SilentlyContinue
        }
        
        Write-Log "Prometheus downloaded and extracted"
    } catch {
        Write-Log "Prometheus install failed: $_" "ERROR"
        exit 1
    }
} else {
    Write-Log "Prometheus already exists, skipping download"
}

# Always copy config from deploy folder to ensure it's correct
if (Test-Path $prometheusConfigSrc) {
    Copy-Item $prometheusConfigSrc -Destination $prometheusConfigDst -Force
    Write-Log "Copied Prometheus config"
}

$oldPrometheus = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
if ($oldPrometheus) {
    Write-Log "Stopping old Prometheus..."
    Stop-Process -Name "prometheus" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$prometheusDataPath = "$InstallRoot\data"
if (-not (Test-Path $prometheusDataPath)) {
    New-Item -ItemType Directory -Path $prometheusDataPath -Force | Out-Null
}

Write-Log "Starting Prometheus..."
$prometheusArgs = "--config.file=`"$prometheusConfigDst`" --storage.tsdb.path=`"$prometheusDataPath`" --web.console.libraries=`"$prometheusPath\console_libraries`" --web.console.templates=`"$prometheusPath\consoles`" --web.listen-address=:9090 --storage.tsdb.retention.time=15d"
$psi3 = New-Object System.Diagnostics.ProcessStartInfo
$psi3.FileName = $prometheusExe
$psi3.Arguments = $prometheusArgs
$psi3.UseShellExecute = $false
[System.Diagnostics.Process]::Start($psi3) | Out-Null
Start-Sleep -Seconds 5

$prometheusCheck = try { Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($prometheusCheck.StatusCode -eq 200) {
    Write-Log "Prometheus started (http://localhost:9090)"
} else {
    Write-Log "Prometheus may not have started properly" "WARN"
}

# 3. Install Grafana
Write-Host "" -ForegroundColor Yellow
Write-Host "[3/4] Installing Grafana..." -ForegroundColor Yellow

$grafanaPath = "$InstallRoot\grafana"
$grafanaBinPath = "$grafanaPath\bin\grafana-server.exe"
$grafanaUrl = "https://dl.grafana.com/oss/release/grafana-10.1.0.windows-amd64.zip"
$grafanaConfigSrc = "$ScriptDir\deploy\grafana"
$grafanaDataPath = "$InstallRoot\grafana-data"

if (-not (Test-Path $grafanaPath)) {
    New-Item -ItemType Directory -Path $grafanaPath -Force | Out-Null
}

if (-not (Test-Path $grafanaBinPath)) {
    Write-Log "Downloading Grafana..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $zipPath = "$DownloadRoot\grafana-10.1.0.windows-amd64.zip"
        Invoke-WebRequest -Uri $grafanaUrl -OutFile $zipPath -TimeoutSec 300 -UseBasicParsing
        
        Write-Log "Extracting Grafana..."
        Expand-Archive -Path $zipPath -DestinationPath $grafanaPath -Force
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        
        # Move contents from subfolder to root
        $extractedFolder = Get-ChildItem -Path $grafanaPath -Directory | Where-Object { $_.Name -like "grafana*" } | Select-Object -First 1
        if ($extractedFolder -and $extractedFolder.Name -ne "") {
            Get-ChildItem -Path $extractedFolder.FullName | Move-Item -Destination $grafanaPath -Force -ErrorAction SilentlyContinue
            Remove-Item $extractedFolder.FullName -Force -ErrorAction SilentlyContinue
        }
        
        Write-Log "Grafana downloaded and extracted"
    } catch {
        Write-Log "Grafana install failed: $_" "ERROR"
    }
} else {
    Write-Log "Grafana already exists, skipping download"
}

if (-not (Test-Path $grafanaDataPath)) {
    New-Item -ItemType Directory -Path $grafanaDataPath -Force | Out-Null
}

$oldGrafana = Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue
if ($oldGrafana) {
    Write-Log "Stopping old Grafana..."
    Stop-Process -Name "grafana-server" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Log "Starting Grafana..."
$grafanaHome = "$grafanaPath"
$grafanaArgs = "cfg:default.paths.home=`"$grafanaHome`" cfg:default.paths.data=`"$grafanaDataPath`" cfg:default.paths.logs=`"$grafanaDataPath\logs`" cfg:default.server.http_port=3000"
$psi4 = New-Object System.Diagnostics.ProcessStartInfo
$psi4.FileName = $grafanaBinPath
$psi4.Arguments = $grafanaArgs
$psi4.WorkingDirectory = $grafanaPath
$psi4.UseShellExecute = $false
[System.Diagnostics.Process]::Start($psi4) | Out-Null
Start-Sleep -Seconds 5

$grafanaCheck = try { Invoke-WebRequest -Uri "http://localhost:3000/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($grafanaCheck.StatusCode -eq 200) {
    Write-Log "Grafana started (http://localhost:3000)"
    
    # Reset admin password to ensure it's admin123
    Write-Log "Resetting Grafana admin password..."
    Set-Location $grafanaPath
    $resetResult = & "$grafanaBinPath" admin reset-admin-password admin123 2>&1 | Out-String
    if ($resetResult -match "successfully") {
        Write-Log "Grafana admin password reset successfully"
    }
} else {
    Write-Log "Grafana may not have started properly" "WARN"
}

# 4. Configure Grafana
Write-Host "" -ForegroundColor Yellow
Write-Host "[4/4] Configuring Grafana..." -ForegroundColor Yellow

Write-Log "Configuring Grafana datasources and dashboards..."
$datasourceDir = "$grafanaDataPath\provisioning\datasources"
$dashboardDir = "$grafanaDataPath\provisioning\dashboards"

if (-not (Test-Path $datasourceDir)) {
    New-Item -ItemType Directory -Path $datasourceDir -Force | Out-Null
}
if (-not (Test-Path $dashboardDir)) {
    New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null
}

if (Test-Path "$grafanaConfigSrc\provisioning\datasources\prometheus.yml") {
    Copy-Item "$grafanaConfigSrc\provisioning\datasources\prometheus.yml" "$datasourceDir\prometheus.yml" -Force -ErrorAction SilentlyContinue
}

if (Test-Path "$grafanaConfigSrc\provisioning\dashboards") {
    Copy-Item "$grafanaConfigSrc\provisioning\dashboards\*" "$dashboardDir\" -Force -Recurse -ErrorAction SilentlyContinue
}

Write-Log "Grafana configuration complete"

# Done
Write-Host "" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Access URLs:" -ForegroundColor White
Write-Host "  - Prometheus:   http://localhost:9090" -ForegroundColor Cyan
Write-Host "  - Grafana:      http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - windows_exporter: http://localhost:9182/metrics" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Credentials:" -ForegroundColor White
Write-Host "  - Grafana: admin / admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Install directory: $InstallRoot" -ForegroundColor White
Write-Host ""
Write-Host "  Next run will start services directly without re-downloading" -ForegroundColor Yellow
Write-Host ""
Write-Host "  To uninstall: .\start-prometheus.ps1 -Uninstall" -ForegroundColor White
Write-Host ""

Write-Log "========== Setup Complete =========="

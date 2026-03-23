$ErrorActionPreference = "Stop"

Write-Host "Starting Grafana with correct paths..."

$grafanaHome = "C:\Prometheus\grafana"
$grafanaData = "C:\Prometheus\grafana\data"
$grafanaLogs = "C:\Prometheus\grafana\data\log"

if (-not (Test-Path $grafanaData)) {
    New-Item -ItemType Directory -Path $grafanaData -Force | Out-Null
}
if (-not (Test-Path $grafanaLogs)) {
    New-Item -ItemType Directory -Path $grafanaLogs -Force | Out-Null
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "$grafanaHome\bin\grafana-server.exe"
$psi.Arguments = "cfg:default.paths.home=`"$grafanaHome`" cfg:default.paths.data=`"$grafanaData`" cfg:default.paths.logs=`"$grafanaLogs`" cfg:default.server.http_port=3000"
$psi.WorkingDirectory = $grafanaHome
$psi.UseShellExecute = $false
[System.Diagnostics.Process]::Start($psi) | Out-Null

Write-Host "Grafana starting, waiting 5 seconds..."
Start-Sleep -Seconds 5

$check = try { Invoke-WebRequest -Uri "http://localhost:3000/api/health" -TimeoutSec 5 -UseBasicParsing } catch { $null }
if ($check.StatusCode -eq 200) {
    Write-Host "Grafana is healthy!" -ForegroundColor Green
} else {
    Write-Host "Grafana may not be ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Login at http://localhost:3000"
Write-Host "Username: admin"
Write-Host "Password: admin123"

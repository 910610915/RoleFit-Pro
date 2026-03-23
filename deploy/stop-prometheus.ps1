# Prometheus 监控栈停止脚本
# Usage: .\stop-prometheus.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Prometheus 监控栈停止脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到部署目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$deployDir = $scriptDir
if ($scriptDir -notlike "*\deploy") {
    $deployDir = Join-Path $scriptDir "deploy"
}
Set-Location $deployDir

$composeFile = "docker-compose.prometheus.yml"

# 检查文件是否存在
if (-not (Test-Path $composeFile)) {
    Write-Host "错误: $composeFile 未找到" -ForegroundColor Red
    exit 1
}

# 停止服务
Write-Host "停止 Prometheus 监控栈..." -ForegroundColor Yellow
docker-compose -f $composeFile down

if ($LASTEXITCODE -ne 0) {
    Write-Host "警告: Docker Compose 停止时出现问题" -ForegroundColor Red
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  服务已停止" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "提示:" -ForegroundColor Yellow
    Write-Host "  - 如需完全清理数据，运行: docker-compose -f $composeFile down -v" -ForegroundColor White
    Write-Host "  - 如需重新启动，运行: .\start-prometheus.ps1" -ForegroundColor White
    Write-Host ""
}

# Prometheus 监控栈启动脚本
# Usage: .\start-prometheus.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Prometheus 监控栈启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker 是否运行
Write-Host "[1/4] 检查 Docker Desktop 状态..." -ForegroundColor Yellow
$dockerStatus = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: Docker Desktop 未运行或未正确安装" -ForegroundColor Red
    Write-Host "请启动 Docker Desktop 后重试" -ForegroundColor Red
    exit 1
}
Write-Host "Docker 运行正常" -ForegroundColor Green

# 创建网络
Write-Host "[2/4] 创建监控网络..." -ForegroundColor Yellow
$networkExists = docker network ls | Select-String "monitoring"
if (-not $networkExists) {
    docker network create monitoring 2>&1 | Out-Null
    Write-Host "监控网络已创建" -ForegroundColor Green
} else {
    Write-Host "监控网络已存在" -ForegroundColor Green
}

# 切换到部署目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$deployDir = $scriptDir
if ($scriptDir -notlike "*\deploy") {
    $deployDir = Join-Path $scriptDir "deploy"
}
Set-Location $deployDir

# 启动服务
Write-Host "[3/4] 启动 Prometheus 监控栈..." -ForegroundColor Yellow
$composeFile = "docker-compose.prometheus.yml"
if (-not (Test-Path $composeFile)) {
    Write-Host "错误: $composeFile 未找到" -ForegroundColor Red
    exit 1
}

docker-compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "错误: Docker Compose 启动失败" -ForegroundColor Red
    Write-Host "请检查日志: docker-compose -f $composeFile logs" -ForegroundColor Red
    exit 1
}
Write-Host "服务启动成功" -ForegroundColor Green

# 等待服务就绪
Write-Host "[4/4] 等待服务就绪..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查服务状态
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务已启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  - Prometheus:    http://localhost:9090" -ForegroundColor White
Write-Host "  - Grafana:      http://localhost:3000" -ForegroundColor White
Write-Host "  - AlertManager: http://localhost:9093" -ForegroundColor White
Write-Host ""
Write-Host "  Grafana 默认凭据: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "下一步:" -ForegroundColor Cyan
Write-Host "  1. 在目标机器上安装 windows_exporter (deploy\windows_exporter\deploy.bat)" -ForegroundColor White
Write-Host "  2. 访问 Grafana 查看仪表盘" -ForegroundColor White
Write-Host "  3. 查看 Prometheus targets: http://localhost:9090/targets" -ForegroundColor White
Write-Host ""

# 显示容器状态
Write-Host "容器状态:" -ForegroundColor Cyan
docker-compose -f $composeFile ps

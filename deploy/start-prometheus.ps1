# RoleFit Pro Prometheus 监控一键部署脚本
# 功能：自动下载依赖、安装服务、启动监控栈
# 首次运行自动安装，再次运行直接启动
# 无需 Docker！

param(
    [switch]$Uninstall  # 卸载模式
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallRoot = "$env:LOCALAPPDATA\RoleFitPrometheus"
$LogFile = "$InstallRoot\install.log"

# 颜色定义
function Write-ColorOutput {
    param($Message, $Color = "White")
    $colors = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
    }
    Write-Host $Message -ForegroundColor $colors[$Color]
}

# 日志函数
function Write-Log {
    param($Message, $Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8 -ErrorAction SilentlyContinue
    Write-ColorOutput $logMessage "Cyan"
}

# 卸载模式
if ($Uninstall) {
    Write-ColorOutput "========================================" "Yellow"
    Write-ColorOutput "  Prometheus 监控卸载" "Yellow"
    Write-ColorOutput "========================================" "Yellow"
    Write-ColorOutput ""

    Write-Log "停止 Prometheus 服务..."
    $prometheusProc = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
    if ($prometheusProc) { Stop-Process -Name "prometheus" -Force -ErrorAction SilentlyContinue }
    
    Write-Log "停止 Grafana 服务..."
    $grafanaProc = Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue
    if ($grafanaProc) { Stop-Process -Name "grafana-server" -Force -ErrorAction SilentlyContinue }

    Write-Log "停止 windows_exporter 服务..."
    if (Get-Service -Name "winExporter" -ErrorAction SilentlyContinue) {
        Stop-Service -Name "winExporter" -Force -ErrorAction SilentlyContinue
        sc.exe delete winExporter -ErrorAction SilentlyContinue
    }
    $winExporterProc = Get-Process -Name "windows_exporter" -ErrorAction SilentlyContinue
    if ($winExporterProc) { Stop-Process -Name "windows_exporter" -Force -ErrorAction SilentlyContinue }

    Write-Log "清理安装目录..."
    if (Test-Path $InstallRoot) {
        Start-Sleep -Seconds 2
        Remove-Item -Path $InstallRoot -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-ColorOutput ""
    Write-ColorOutput "========================================" "Green"
    Write-ColorOutput "  卸载完成" "Green"
    Write-ColorOutput "========================================" "Green"
    exit 0
}

Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput "  RoleFit Pro Prometheus 监控一键部署" "Cyan"
Write-ColorOutput "========================================" "Cyan"
Write-ColorOutput ""

# 确保安装目录存在
if (-not (Test-Path $InstallRoot)) {
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
}

Write-Log "安装目录: $InstallRoot"
Write-Log "========== 开始部署 =========="
Write-Log "首次运行将自动下载所有依赖..."

# 检查 PowerShell 版本
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Log "错误: 需要 PowerShell 5.0 或更高版本" "ERROR"
    Write-Log "当前版本: $($PSVersionTable.PSVersion)" "ERROR"
    exit 1
}

# ========== 1. 安装 windows_exporter ==========
Write-ColorOutput "" "Yellow"
Write-ColorOutput "[1/4] 安装 windows_exporter..." "Yellow"

$winExporterPath = "$InstallRoot\windows_exporter"
$winExporterExe = "$winExporterPath\windows_exporter.exe"
$winExporterUrl = "https://github.com/prometheus-community/windows_exporter/releases/download/v0.25.0/windows_exporter-0.25.0-amd64.exe"

if (-not (Test-Path $winExporterPath)) {
    New-Item -ItemType Directory -Path $winExporterPath -Force | Out-Null
}

if (-not (Test-Path $winExporterExe)) {
    Write-Log "下载 windows_exporter..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $winExporterUrl -OutFile $winExporterExe -TimeoutSec 120 -UseBasicParsing
        Write-Log "windows_exporter 下载完成"
    } catch {
        Write-Log "windows_exporter 下载失败: $_" "ERROR"
        Write-Log "请手动下载: $winExporterUrl" "ERROR"
        exit 1
    }
} else {
    Write-Log "windows_exporter 已存在，跳过下载"
}

# 注册并启动 windows_exporter 服务
$winExporterService = Get-Service -Name "winExporter" -ErrorAction SilentlyContinue
if (-not $winExporterService) {
    Write-Log "注册 windows_exporter 服务..."
    $installArgs = "--install", "--name", "winExporter", "--display-name", "Windows Exporter", "--description", "Prometheus Windows Exporter", "--", "--collectors.enabled", "cpu,cs,logical_disk,memory,net,os,system,gpu,nvidia", "--telemetry.port", "9182"
    $proc = Start-Process -FilePath $winExporterExe -ArgumentList $installArgs -Wait -NoNewWindow -PassThru -Verb RunAs -ErrorAction SilentlyContinue
    if ($proc -and $proc.ExitCode -eq 0) {
        Write-Log "windows_exporter 服务注册成功"
    } else {
        Write-Log "服务注册需要管理员权限，将直接启动进程..." "WARN"
    }
}

# 停止旧进程
$oldWinExporter = Get-Process -Name "windows_exporter" -ErrorAction SilentlyContinue
if ($oldWinExporter) {
    Stop-Process -Name "windows_exporter" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 启动 windows_exporter
Write-Log "启动 windows_exporter..."
Start-Process -FilePath $winExporterExe -ArgumentList "--collectors.enabled cpu,cs,logical_disk,memory,net,os,system,gpu,nvidia", "--telemetry.port 9182" -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 验证
$winExporterCheck = try { Invoke-WebRequest -Uri "http://localhost:9182/metrics" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($winExporterCheck) {
    Write-Log "windows_exporter 启动成功 (http://localhost:9182/metrics)"
} else {
    Write-Log "windows_exporter 可能未正常启动" "WARN"
}

# ========== 2. 安装 Prometheus ==========
Write-ColorOutput "" "Yellow"
Write-ColorOutput "[2/4] 安装 Prometheus..." "Yellow"

$prometheusPath = "$InstallRoot\prometheus"
$prometheusExe = "$prometheusPath\prometheus.exe"
$prometheusConfig = "$ScriptDir\deploy\prometheus\prometheus.yml"
$prometheusUrl = "https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.windows-amd64.tar.gz"

if (-not (Test-Path $prometheusPath)) {
    New-Item -ItemType Directory -Path $prometheusPath -Force | Out-Null
}

if (-not (Test-Path $prometheusExe)) {
    Write-Log "下载 Prometheus..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $tarPath = "$InstallRoot\prometheus-2.47.0.windows-amd64.tar.gz"
        Invoke-WebRequest -Uri $prometheusUrl -OutFile $tarPath -TimeoutSec 300 -UseBasicParsing
        
        Write-Log "解压 Prometheus..."
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $tar = [System.IO.Compression.ZipFile]::OpenRead($tarPath)
        $tar.Entries | ForEach-Object {
            $entryPath = Join-Path $prometheusPath $_.FullName
            $entryDir = Split-Path $entryPath -Parent
            if (-not (Test-Path $entryDir)) { New-Item -ItemType Directory -Path $entryDir -Force | Out-Null }
            if ($_.Name -ne "") { [System.IO.Compression.ZipFileExtensions]::ExtractToFile($_, $entryPath, $true) }
        }
        $tar.Dispose()
        Remove-Item $tarPath -Force -ErrorAction SilentlyContinue
        
        # 重命名目录结构
        $extractedFolder = Get-ChildItem -Path $prometheusPath -Directory | Where-Object { $_.Name -like "prometheus*" } | Select-Object -First 1
        if ($extractedFolder -and $extractedFolder.Name -ne "") {
            Get-ChildItem -Path $extractedFolder.FullName | Move-Item -Destination $prometheusPath -Force -ErrorAction SilentlyContinue
            Remove-Item $extractedFolder.FullName -Force -ErrorAction SilentlyContinue
        }
        
        Write-Log "Prometheus 下载并解压完成"
    } catch {
        Write-Log "Prometheus 安装失败: $_" "ERROR"
        Write-Log "请手动下载: $prometheusUrl" "ERROR"
        exit 1
    }
} else {
    Write-Log "Prometheus 已存在，跳过下载"
}

# 复制配置文件
if ((Test-Path $prometheusConfig) -and (-not (Test-Path "$prometheusPath\prometheus.yml"))) {
    Copy-Item $prometheusConfig "$prometheusPath\prometheus.yml" -Force
    Write-Log "复制 Prometheus 配置文件"
}

# 停止旧的 Prometheus
$oldPrometheus = Get-Process -Name "prometheus" -ErrorAction SilentlyContinue
if ($oldPrometheus) {
    Stop-Process -Name "prometheus" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 创建数据目录
$prometheusDataPath = "$InstallRoot\data"
if (-not (Test-Path $prometheusDataPath)) {
    New-Item -ItemType Directory -Path $prometheusDataPath -Force | Out-Null
}

# 启动 Prometheus
Write-Log "启动 Prometheus..."
$prometheusArgs = @(
    "--config.file=`"$prometheusPath\prometheus.yml`"",
    "--storage.tsdb.path=`"$prometheusDataPath`"",
    "--web.console.libraries=`"$prometheusPath\console_libraries`"",
    "--web.console.templates=`"$prometheusPath\consoles`"",
    "--web.listen-address=`:9090`",
    "--storage.tsdb.retention.time=15d"
)
Start-Process -FilePath $prometheusExe -ArgumentList ($prometheusArgs -join " ") -WindowStyle Hidden
Start-Sleep -Seconds 3

# 检查 Prometheus 是否启动成功
$prometheusCheck = try { Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($prometheusCheck.StatusCode -eq 200) {
    Write-Log "Prometheus 启动成功 (http://localhost:9090)"
} else {
    Write-Log "Prometheus 可能未正常启动，请检查 http://localhost:9090" "WARN"
}

# ========== 3. 安装 Grafana ==========
Write-ColorOutput "" "Yellow"
Write-ColorOutput "[3/4] 安装 Grafana..." "Yellow"

$grafanaPath = "$InstallRoot\grafana"
$grafanaBinPath = "$grafanaPath\bin\grafana-server.exe"
$grafanaUrl = "https://dl.grafana.com/oss/release/grafana-10.1.0.windows-amd64.zip"
$grafanaConfigSrc = "$ScriptDir\deploy\grafana"
$grafanaDataPath = "$InstallRoot\grafana-data"

if (-not (Test-Path $grafanaPath)) {
    New-Item -ItemType Directory -Path $grafanaPath -Force | Out-Null
}

if (-not (Test-Path $grafanaBinPath)) {
    Write-Log "下载 Grafana..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $zipPath = "$InstallRoot\grafana-10.1.0.windows-amd64.zip"
        Invoke-WebRequest -Uri $grafanaUrl -OutFile $zipPath -TimeoutSec 300 -UseBasicParsing
        
        Write-Log "解压 Grafana..."
        Expand-Archive -Path $zipPath -DestinationPath $grafanaPath -Force
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        
        # 重命名目录结构
        $extractedFolder = Get-ChildItem -Path $grafanaPath -Directory | Where-Object { $_.Name -like "grafana*" } | Select-Object -First 1
        if ($extractedFolder -and $extractedFolder.Name -ne "") {
            Get-ChildItem -Path $extractedFolder.FullName | Move-Item -Destination $grafanaPath -Force -ErrorAction SilentlyContinue
            Remove-Item $extractedFolder.FullName -Force -ErrorAction SilentlyContinue
        }
        
        Write-Log "Grafana 下载并解压完成"
    } catch {
        Write-Log "Grafana 安装失败: $_" "ERROR"
        Write-Log "请手动下载: $grafanaUrl" "ERROR"
    }
} else {
    Write-Log "Grafana 已存在，跳过下载"
}

# 创建数据目录
if (-not (Test-Path $grafanaDataPath)) {
    New-Item -ItemType Directory -Path $grafanaDataPath -Force | Out-Null
}

# 停止旧的 Grafana
$oldGrafana = Get-Process -Name "grafana-server" -ErrorAction SilentlyContinue
if ($oldGrafana) {
    Stop-Process -Name "grafana-server" -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 启动 Grafana
Write-Log "启动 Grafana..."
$grafanaArgs = @(
    "cfg:default.paths.data=`"$grafanaDataPath`"",
    "cfg:default.paths.logs=`"$grafanaDataPath\logs`"",
    "cfg:default.server.http_port=3000"
)
Start-Process -FilePath $grafanaBinPath -ArgumentList ($grafanaArgs -join " ") -WindowStyle Hidden -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# 检查 Grafana 是否启动成功
$grafanaCheck = try { Invoke-WebRequest -Uri "http://localhost:3000/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction SilentlyContinue } catch { $null }
if ($grafanaCheck.StatusCode -eq 200) {
    Write-Log "Grafana 启动成功 (http://localhost:3000)"
} else {
    Write-Log "Grafana 可能未正常启动，请检查 http://localhost:3000" "WARN"
}

# ========== 4. 配置 Grafana ==========
Write-ColorOutput "" "Yellow"
Write-ColorOutput "[4/4] 配置 Grafana..." "Yellow"

Write-Log "配置 Grafana 数据源和仪表盘..."
$datasourceDir = "$grafanaDataPath\provisioning\datasources"
$dashboardDir = "$grafanaDataPath\provisioning\dashboards"

if (-not (Test-Path $datasourceDir)) {
    New-Item -ItemType Directory -Path $datasourceDir -Force | Out-Null
}
if (-not (Test-Path $dashboardDir)) {
    New-Item -ItemType Directory -Path $dashboardDir -Force | Out-Null
}

# 复制数据源配置
if (Test-Path "$grafanaConfigSrc\provisioning\datasources\prometheus.yml") {
    Copy-Item "$grafanaConfigSrc\provisioning\datasources\prometheus.yml" "$datasourceDir\prometheus.yml" -Force -ErrorAction SilentlyContinue
}

# 复制 Dashboard 配置
if (Test-Path "$grafanaConfigSrc\provisioning\dashboards") {
    Copy-Item "$grafanaConfigSrc\provisioning\dashboards\*" "$dashboardDir\" -Force -Recurse -ErrorAction SilentlyContinue
}

Write-Log "Grafana 配置完成"

# ========== 完成 ==========
Write-ColorOutput "" "Cyan"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput "  部署完成!" "Green"
Write-ColorOutput "========================================" "Green"
Write-ColorOutput ""
Write-ColorOutput "  访问地址:" "White"
Write-ColorOutput "  - Prometheus:   http://localhost:9090" "Cyan"
Write-ColorOutput "  - Grafana:      http://localhost:3000" "Cyan"
Write-ColorOutput "  - windows_exporter: http://localhost:9182/metrics" "Cyan"
Write-ColorOutput ""
Write-ColorOutput "  默认凭据:" "White"
Write-ColorOutput "  - Grafana: admin / admin123" "Cyan"
Write-ColorOutput ""
Write-ColorOutput "  安装目录: $InstallRoot" "White"
Write-ColorOutput ""
Write-ColorOutput "  下次运行此脚本将直接启动服务，无需重新下载" "Yellow"
Write-ColorOutput ""
Write-ColorOutput "  停止服务命令: .\start-prometheus.ps1 -Uninstall" "White"
Write-ColorOutput ""

Write-Log "========== 部署完成 =========="

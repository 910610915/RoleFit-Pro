# Prometheus 部署指南

> 基于 RoleFit Pro 的 Prometheus 监控系统集成

## 概述

本文档描述如何在 RoleFit Pro 项目中部署 Prometheus 监控系统，实现更精准的硬件指标抓取。

**架构变化：**
- **旧架构：** Push 模式（Agent → API → DB）
- **新架构：** Pull 模式（windows_exporter → Prometheus → Grafana）

## 前提条件

- Docker Desktop for Windows 已安装
- Windows Server 2016+ 或 Windows 10/11
- 至少 4GB RAM 可用
- 目标 Windows 机器需要安装 windows_exporter

## 快速开始

### 1. 启动 Prometheus 监控栈

```powershell
# 在项目根目录执行
cd deploy
.\start-prometheus.ps1
```

### 2. 在目标机器安装 windows_exporter

```powershell
# 以管理员身份运行
cd deploy\windows_exporter
.\deploy.bat
```

### 3. 访问服务

| 服务 | 地址 | 默认凭据 |
|------|------|----------|
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3000 | admin / admin123 |
| windows_exporter | http://localhost:9182/metrics | - |
| AlertManager | http://localhost:9093 | - |

## 架构说明

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ windows_    │────▶│ Prometheus  │────▶│   Grafana   │
│ exporter    │     │   Server   │     │  Dashboard  │
│ :9182       │     │   :9090    │     │   :3000     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ AlertManager│
                    │   :9093     │
                    └─────────────┘
```

### 数据流

1. **windows_exporter** 在每台 Windows 机器上运行，暴露硬件指标
2. **Prometheus Server** 定期从 windows_exporter 拉取指标（默认 15s 间隔）
3. **Grafana** 从 Prometheus 查询数据并展示可视化仪表盘
4. **AlertManager** 接收 Prometheus 告警并发送通知

## 文件结构

```
deploy/
├── docker-compose.prometheus.yml    # Docker Compose 配置
├── prometheus/
│   ├── prometheus.yml              # Prometheus 配置
│   └── alert.rules.yml             # 告警规则
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── prometheus.yml      # Grafana 数据源
│       └── dashboards/
│           ├── dashboard.yml       # Dashboard 配置
│           └── dashboards/
│               └── windows-exporter.json  # Windows 监控面板
├── alertmanager/
│   └── alertmanager.yml            # AlertManager 配置
├── windows_exporter/
│   ├── deploy.bat                  # 安装脚本
│   └── uninstall.bat              # 卸载脚本
├── start-prometheus.ps1            # 启动脚本
└── stop-prometheus.ps1            # 停止脚本
```

## 指标列表

| 指标名称 | 类型 | 说明 |
|----------|------|------|
| windows_cpu_percent | Gauge | CPU 使用率 (%) |
| windows_memory_percent | Gauge | 内存使用率 (%) |
| windows_disk_read_bytes_total | Counter | 磁盘读取字节数 |
| windows_disk_write_bytes_total | Counter | 磁盘写入字节数 |
| windows_network_sent_bytes_total | Counter | 网络发送字节数 |
| windows_network_recv_bytes_total | Counter | 网络接收字节数 |
| windows_gpu_percent | Gauge | GPU 使用率 (%) |
| windows_gpu_temperature_celsius | Gauge | GPU 温度 (°C) |
| windows_cpu_temperature_celsius | Gauge | CPU 温度 (°C) |

### GPU 指标要求

GPU 指标需要 NVIDIA 驱动和 nvidia-smi 支持。windows_exporter 会自动检测并暴露以下 GPU 指标：

- `windows_gpu_percent` - GPU 利用率
- `windows_gpu_temperature_celsius` - GPU 温度
- `windows_gpu_memory_percent` - 显存使用率
- `windows_gpu_power_watts` - GPU 功耗

## 告警规则

参考 `deploy/prometheus/alert.rules.yml` 中的预配置告警规则。

### 预配置告警

| 告警名称 | 条件 | 严重程度 |
|----------|------|----------|
| HighCPU | cpu > 90% for 5m | warning |
| CriticalCPU | cpu > 95% for 2m | critical |
| HighMemory | memory > 90% for 5m | warning |
| CriticalMemory | memory > 95% for 2m | critical |
| HighGPUTemperature | gpu_temp > 85°C for 5m | critical |
| DeviceDown | 设备离线 > 2m | critical |

## 配置 Prometheus 目标

编辑 `deploy/prometheus/prometheus.yml` 添加新的监控目标：

```yaml
scrape_configs:
  - job_name: 'windows_exporter'
    static_configs:
      - targets:
          - 'localhost:9182'           # 本机
          - '192.168.1.101:9182'      # 远程机器
          - 'DESKTOP-PC:9182'          # 主机名
        labels:
          group: 'windows'
```

修改配置后重载 Prometheus：
```powershell
Invoke-RestMethod -Uri http://localhost:9090/-/reload -Method Post
```

## 前端集成

### 环境变量

在 `frontend/.env` 中配置：

```env
VITE_GRAFANA_URL=http://localhost:3000
VITE_PROMETHEUS_URL=http://localhost:9090
```

### 组件使用

#### GrafanaPanel 组件

```vue
<GrafanaPanel
  dashboard-uid="windows-exporter"
  :device-id="selectedInstance"
  :height="400"
/>
```

#### usePrometheus Hook

```typescript
import { usePrometheus } from '@/composables/usePrometheus'

const { getCpuPercent, getMemoryPercent, getLatestMetrics } = usePrometheus()

// 获取历史数据
const cpuData = await getCpuPercent('DESKTOP-PC', 60)

// 获取当前值
const metrics = await getLatestMetrics('DESKTOP-PC')
```

## 故障排除

### windows_exporter 无法启动

1. 检查端口占用：`netstat -an | findstr 9182`
2. 以管理员身份运行安装命令
3. 检查服务状态：`Get-Service winExporter`
4. 查看日志：事件查看器 → Windows 日志 → 应用程序

### Prometheus 无法抓取

1. 检查防火墙设置
2. 验证目标机器端口可访问：
   ```powershell
   Invoke-WebRequest -Uri http://target:9182/metrics
   ```
3. 检查 PrometheusTargets 页面：http://localhost:9090/targets
4. 查看 Prometheus 日志：`docker logs prometheus`

### Grafana 仪表盘空白

1. 确认 Prometheus 数据源已配置
2. 检查查询的指标名称是否正确
3. 验证时间范围设置
4. 检查浏览器控制台错误

### Docker 容器无法启动

1. 检查 Docker Desktop 是否运行
2. 查看容器日志：`docker-compose -f docker-compose.prometheus.yml logs`
3. 检查端口占用情况

## 维护

### 数据保留

Prometheus 默认保留 15 天数据。如需修改，编辑 `docker-compose.prometheus.yml`：

```yaml
command:
  - '--config.file=/etc/prometheus/prometheus.yml'
  - '--storage.tsdb.retention.time=30d'  # 改为 30 天
```

### 更新 windows_exporter

```powershell
# 停止服务
.\uninstall.bat

# 重新安装
.\deploy.bat
```

### 备份 Grafana 数据

```powershell
docker stop grafana
docker run --rm -v grafana_data:/data -v $(pwd):/backup busybox tar czf /backup/grafana-backup.tar.gz /data
docker start grafana
```

## 卸载

### 停止监控栈

```powershell
.\stop-prometheus.ps1
```

### 卸载 windows_exporter

```powershell
cd deploy\windows_exporter
.\uninstall.bat
```

### 清理 Docker 卷

```powershell
docker volume rm prometheus_prometheus_data grafana_grafana_data
docker network rm monitoring
```

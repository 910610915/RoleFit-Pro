# Prometheus 监控系统集成实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将监控系统从当前 Push 模式（Agent → API → DB）迁移到 Prometheus Pull 模式，实现更精准的硬件指标抓取。

**Architecture:** 
- 部署 Prometheus Server + Grafana 用于指标存储和可视化
- 部署 windows_exporter（官方工具）用于 Windows 硬件指标采集
- Agent 改为负责任务执行，指标采集由 windows_exporter 负责
- 后端 API 改为查询 Prometheus 获取监控数据

**Tech Stack:** 
- Prometheus Server (时序数据库)
- Grafana (可视化仪表盘)
- windows_exporter (Windows 指标导出器)
- prometheus_client (Python SDK)

---

## Phase 1: 环境准备与基础设施

### Task 1: 创建 Prometheus 配置文件

**Files:**
- Create: `deploy/prometheus/prometheus.yml`

**Step 1: 创建目录结构**

```bash
mkdir -p deploy/prometheus
mkdir -p deploy/grafana/provisioning/datasources
mkdir -p deploy/grafana/provisioning/dashboards
```

**Step 2: 创建 prometheus.yml**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Windows Exporter 抓取配置
  - job_name: 'windows_exporter'
    static_configs:
      - targets: ['localhost:9182']
        labels:
          group: 'windows'
    
  # 我们的 Server 指标（如果有）
  - job_name: 'rolefit_server'
    static_configs:
      - targets: ['backend:8000']
        labels:
          group: 'server'
    
  # Agent 指标（如果使用 prometheus_client）
  - job_name: 'rolefit_agent'
    static_configs:
      - targets: ['localhost:9100']
        labels:
          group: 'agent'
```

**Step 3: 提交**

```bash
git add deploy/prometheus/prometheus.yml
git commit -m "feat(prometheus): 添加 Prometheus 配置文件"
```

---

### Task 2: 创建 Grafana 数据源配置

**Files:**
- Create: `deploy/grafana/provisioning/datasources/prometheus.yml`

**Step 1: 创建数据源配置**

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

**Step 2: 提交**

```bash
git add deploy/grafana/provisioning/datasources/prometheus.yml
git commit -m "feat(grafana): 添加 Prometheus 数据源配置"
```

---

### Task 3: 创建 Grafana Dashboard 配置

**Files:**
- Create: `deploy/grafana/provisioning/dashboards/dashboard.yml`
- Create: `deploy/grafana/provisioning/dashboards/windows-exporter.json`

**Step 1: 创建 dashboard 配置**

```yaml
apiVersion: 1

providers:
  - name: 'RoleFit Dashboards'
    orgId: 1
    folder: ''
    folderUid: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

**Step 2: 创建 Windows Exporter 监控面板**

创建 `deploy/grafana/provisioning/dashboards/windows-exporter.json`，包含：
- CPU 使用率
- 内存使用率
- 磁盘 IO
- 网络流量
- GPU 指标（如果可用）

**Step 3: 提交**

```bash
git add deploy/grafana/provisioning/dashboards/
git commit -m "feat(grafana): 添加 Windows 监控 Dashboard"
```

---

### Task 4: 创建 Docker Compose 配置

**Files:**
- Create: `deploy/docker-compose.prometheus.yml`

**Step 1: 创建完整的 docker-compose 配置**

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:10.1.0
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped
    networks:
      - monitoring
    depends_on:
      - prometheus

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

**Step 2: 提交**

```bash
git add deploy/docker-compose.prometheus.yml
git commit -m "feat(prometheus): 添加 Docker Compose 配置"
```

---

## Phase 2: Agent 改造

### Task 5: 创建 windows_exporter 部署脚本

**Files:**
- Create: `deploy/windows_exporter/deploy.bat`

**Step 1: 创建 Windows 部署脚本**

```batch
@echo off
setlocal

set "EXPORTER_VERSION=0.28.1"
set "INSTALL_DIR=C:\Program Files\windows_exporter"
set "PORT=9182"

echo Installing windows_exporter %EXPORTER_VERSION%...

:: Download if not exists
if not exist "windows_exporter-%EXPORTER_VERSION%-amd64.exe" (
    echo Downloading windows_exporter...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/prometheus/windows_exporter/releases/download/v%EXPORTER_VERSION%/windows_exporter-%EXPORTER_VERSION%-amd64.exe' -OutFile 'windows_exporter-%EXPORTER_VERSION%-amd64.exe'"
)

:: Create install directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

:: Copy exporter
copy "windows_exporter-%EXPORTER_VERSION%-amd64.exe" "%INSTALL_DIR%\windows_exporter.exe"

:: Install as service
"%INSTALL_DIR%\windows_exporter.exe" --collectors.enabled=cpu,cs,logical_disk,memory,net,thermalzone,gpu --service.install --service.name="windows_exporter"

:: Start service
net start windows_exporter

echo.
echo windows_exporter installed successfully!
echo Access metrics at: http://localhost:%PORT%/metrics
echo.
echo Grafana dashboard: http://localhost:3000

endlocal
```

**Step 2: 提交**

```bash
git add deploy/windows_exporter/
git commit -m "feat(agent): 添加 windows_exporter 部署脚本"
```

---

### Task 6: 创建 Agent Prometheus Client 版本（可选）

**Files:**
- Create: `agent/prometheus_agent.py`

**Step 1: 创建 Prometheus Client 版本 Agent**

如果用户不想安装 windows_exporter，提供基于 prometheus_client 的 Python 版本：

```python
"""
Prometheus Agent - Alternative to windows_exporter
使用 prometheus_client 暴露指标
"""

from prometheus_client import start_http_server, Gauge, Counter, Info
import psutil
import time
import platform
import subprocess
import json

# 指标定义
CPU_PERCENT = Gauge('windows_cpu_percent', 'CPU usage percent', ['instance'])
MEMORY_PERCENT = Gauge('windows_memory_percent', 'Memory usage percent', ['instance'])
DISK_READ = Gauge('windows_disk_read_bytes', 'Disk read bytes per second', ['instance', 'disk'])
DISK_WRITE = Gauge('windows_disk_write_bytes', 'Disk write bytes per second', ['instance', 'disk'])
NETWORK_SENT = Gauge('windows_network_sent_bytes', 'Network sent bytes', ['instance', 'interface'])
NETWORK_RECV = Gauge('windows_network_recv_bytes', 'Network received bytes', ['instance', 'interface'])
GPU_PERCENT = Gauge('windows_gpu_percent', 'GPU usage percent', ['instance'])
GPU_TEMPERATURE = Gauge('windows_gpu_temperature_celsius', 'GPU temperature', ['instance'])
CPU_TEMPERATURE = Gauge('windows_cpu_temperature_celsius', 'CPU temperature', ['instance'])

SYSTEM_INFO = Info('windows_system', 'System information')
HARDWARE_INFO = Info('windows_hardware', 'Hardware information')

def get_cpu_temp_wmi():
    """通过 WMI 获取 CPU 温度（如果可用）"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             'Add-Type -AssemblyName System.Windows.Forms; ' +
             '[System.Windows.Forms.SystemInformation]::ComputerName'],
            capture_output=True, text=True, timeout=5
        )
        # 实际实现需要调用 WMI
        return None
    except:
        return None

def collect_metrics():
    """收集系统指标"""
    instance = platform.node()
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    CPU_PERCENT.labels(instance=instance).set(cpu_percent)
    
    # Memory
    mem = psutil.virtual_memory()
    MEMORY_PERCENT.labels(instance=instance).set(mem.percent)
    
    # Disk IO
    for disk in psutil.disk_io_counters(perdisk=True):
        DISK_READ.labels(instance=instance, disk=disk).set(disk.read_bytes)
        DISK_WRITE.labels(instance=instance, disk=disk).set(disk.write_bytes)
    
    # Network
    for iface, stats in psutil.net_io_counters(pernic=True).items():
        NETWORK_SENT.labels(instance=instance, interface=iface).set(stats.bytes_sent)
        NETWORK_RECV.labels(instance=instance, interface=iface).set(stats.bytes_recv)
    
    # GPU (如果可用，通过 nvidia-smi)
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(',')
            GPU_PERCENT.labels(instance=instance).set(float(parts[0]))
            GPU_TEMPERATURE.labels(instance=instance).set(float(parts[1]))
    except:
        pass
    
    # CPU Temperature
    cpu_temp = get_cpu_temp_wmi()
    if cpu_temp:
        CPU_TEMPERATURE.labels(instance=instance).set(cpu_temp)
    
    # System Info
    SYSTEM_INFO.info({
        'os': platform.system(),
        'os_version': platform.version(),
        'architecture': platform.machine(),
        'python_version': platform.python_version()
    })

def main():
    port = int(os.environ.get('EXPORTER_PORT', 9100))
    print(f"Starting Prometheus exporter on port {port}")
    start_http_server(port)
    
    print(f"Metrics available at http://localhost:{port}/metrics")
    
    while True:
        collect_metrics()
        time.sleep(15)  # 15秒间隔

if __name__ == '__main__':
    main()
```

**Step 2: 提交**

```bash
git add agent/prometheus_agent.py
git commit -m "feat(agent): 添加 Prometheus Client 版本的 Agent"
```

---

## Phase 3: 后端改造

### Task 7: 安装 Prometheus Python SDK

**Files:**
- Modify: `backend/requirements.txt`

**Step 1: 添加依赖**

```
prometheus-client>=0.17.0
prometheus-api-client>=0.17.0
```

**Step 2: 安装依赖**

```bash
cd backend
pip install prometheus-client prometheus-api-client
```

**Step 3: 提交**

```bash
git add backend/requirements.txt
git commit -m "chore(deps): 添加 prometheus-client 依赖"
```

---

### Task 8: 创建 Prometheus 查询服务

**Files:**
- Create: `backend/app/services/prometheus_service.py`

**Step 1: 创建 Prometheus 查询服务**

```python
"""
Prometheus 查询服务
用于从 Prometheus 获取监控数据
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from prometheus_api_client import PrometheusConnect
from prometheus_client import Metric

class PrometheusService:
    def __init__(self):
        self.prometheus_url = os.environ.get(
            'PROMETHEUS_URL', 
            'http://localhost:9090'
        )
        self.client = PrometheusConnect(url=self.prometheus_url)
    
    def query(self, query: str, time: Optional[str] = None) -> Dict:
        """执行即时查询"""
        return self.client.custom_query(query=query, time=time)
    
    def query_range(
        self, 
        query: str, 
        start_time: datetime, 
        end_time: datetime, 
        step: str = '15s'
    ) -> Dict:
        """执行范围查询"""
        return self.client.custom_query_range(
            query=query,
            start_time=start_time,
            end_time=end_time,
            step=step
        )
    
    def get_cpu_percent(
        self, 
        device_id: str, 
        start: datetime, 
        end: datetime
    ) -> List[Dict]:
        """获取 CPU 使用率"""
        query = f'windows_cpu_percent{{instance="{device_id}"}}'
        data = self.query_range(query, start, end)
        return self._format_range_data(data)
    
    def get_memory_percent(
        self, 
        device_id: str, 
        start: datetime, 
        end: datetime
    ) -> List[Dict]:
        """获取内存使用率"""
        query = f'windows_memory_percent{{instance="{device_id}"}}'
        data = self.query_range(query, start, end)
        return self._format_range_data(data)
    
    def get_gpu_metrics(
        self, 
        device_id: str, 
        start: datetime, 
        end: datetime
    ) -> Dict[str, List[Dict]]:
        """获取 GPU 指标"""
        gpu_util = self.query_range(
            f'windows_gpu_percent{{instance="{device_id}"}}',
            start, end
        )
        gpu_temp = self.query_range(
            f'windows_gpu_temperature_celsius{{instance="{device_id}"}}',
            start, end
        )
        return {
            'utilization': self._format_range_data(gpu_util),
            'temperature': self._format_range_data(gpu_temp)
        }
    
    def get_cpu_temperature(
        self, 
        device_id: str
    ) -> Optional[float]:
        """获取 CPU 温度"""
        query = f'windows_cpu_temperature_celsius{{instance="{device_id}"}}'
        data = self.query(query)
        if data and len(data) > 0:
            return float(data[0]['value'][1])
        return None
    
    def _format_range_data(self, data: Dict) -> List[Dict]:
        """格式化范围查询数据"""
        if not data or 'data' not in data:
            return []
        
        result = []
        for item in data.get('data', {}).get('result', []):
            metric_name = item['metric'].get('__name__', '')
            for timestamp, value in item['values']:
                result.append({
                    'timestamp': datetime.fromtimestamp(timestamp),
                    'value': float(value),
                    'metric': metric_name
                })
        return result

# 全局实例
prometheus_service = PrometheusService()
```

**Step 2: 提交**

```bash
git add backend/app/services/prometheus_service.py
git commit -m "feat(backend): 添加 Prometheus 查询服务"
```

---

### Task 9: 创建 Prometheus 监控 API 端点

**Files:**
- Create: `backend/app/api/prometheus_metrics.py`
- Modify: `backend/app/main.py` (注册路由)

**Step 1: 创建 API 端点**

```python
"""
Prometheus 监控数据 API
替代原有的 /performance/metrics 接口
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from app.services.prometheus_service import prometheus_service

router = APIRouter(prefix="/prometheus", tags=["Prometheus"])

@router.get("/metrics/latest")
def get_latest_metrics(device_id: str):
    """
    获取设备最新监控指标
    从 Prometheus 查询最新数据
    """
    try:
        now = datetime.now()
        
        cpu = prometheus_service.query(
            f'windows_cpu_percent{{instance="{device_id}"}}'
        )
        memory = prometheus_service.query(
            f'windows_memory_percent{{instance="{device_id}"}}'
        )
        
        return {
            'device_id': device_id,
            'timestamp': now.isoformat(),
            'cpu_percent': float(cpu[0]['value'][1]) if cpu else None,
            'memory_percent': float(memory[0]['value'][1]) if memory else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/history")
def get_metrics_history(
    device_id: str,
    metric: str = Query(..., description="指标名称: cpu, memory, gpu, disk, network"),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    step: str = Query('15s', description="查询步长")
):
    """
    获取历史监控数据
    从 Prometheus 查询指定时间范围的数据
    """
    if not start:
        start = datetime.now() - timedelta(hours=1)
    if not end:
        end = datetime.now()
    
    query_map = {
        'cpu': f'windows_cpu_percent{{instance="{device_id}"}}',
        'memory': f'windows_memory_percent{{instance="{device_id}"}}',
        'gpu': f'windows_gpu_percent{{instance="{device_id}"}}',
        'gpu_temp': f'windows_gpu_temperature_celsius{{instance="{device_id}"}}',
        'cpu_temp': f'windows_cpu_temperature_celsius{{instance="{device_id}"}}',
    }
    
    query = query_map.get(metric)
    if not query:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric}")
    
    data = prometheus_service.query_range(query, start, end, step)
    
    return {
        'device_id': device_id,
        'metric': metric,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'data': prometheus_service._format_range_data(data)
    }

@router.get("/alerts")
def get_alerts():
    """获取当前告警"""
    # 可以集成 AlertManager
    return {'alerts': []}
```

**Step 2: 在 main.py 注册路由**

```python
# 在 backend/app/main.py 中添加
from app.api.prometheus_metrics import router as prometheus_router

app.include_router(prometheus_router)
```

**Step 3: 提交**

```bash
git add backend/app/api/prometheus_metrics.py
git add backend/app/main.py  # 只添加路由注册部分
git commit -m "feat(backend): 添加 Prometheus 监控 API 端点"
```

---

### Task 10: 标记旧 API 为废弃

**Files:**
- Modify: `backend/app/api/performance.py`

**Step 1: 添加废弃警告**

```python
"""
Performance Metrics API

DEPRECATED: 此模块将在未来版本中移除。
请使用 /api/prometheus/* 接口获取监控数据。

迁移指南:
  - GET /api/performance/metrics -> GET /api/prometheus/metrics/latest
  - GET /api/performance/metrics/history -> GET /api/prometheus/metrics/history
"""

import warnings
warnings.warn(
    "performance API is deprecated, use /api/prometheus instead",
    DeprecationWarning,
    stacklevel=2
)
```

**Step 2: 提交**

```bash
git add backend/app/api/performance.py
git commit -m "chore(backend): 标记 performance API 为废弃"
```

---

## Phase 4: 前端改造

### Task 11: 创建 Grafana iframe 集成组件

**Files:**
- Create: `frontend/src/components/GrafanaPanel.vue`

**Step 1: 创建 Grafana 面板组件**

```vue
<template>
  <div class="grafana-panel">
    <div class="panel-header" v-if="title">
      <h3>{{ title }}</h3>
      <n-button size="small" @click="openGrafana">
        <template #icon>
          <n-icon><ExternalLinkOutline /></n-icon>
        </template>
        在 Grafana 中打开
      </n-button>
    </div>
    
    <div class="panel-content">
      <iframe
        v-if="grafanaUrl"
        :src="embeddedUrl"
        :width="width"
        :height="height"
        frameborder="0"
      />
      
      <n-empty v-else description="Grafana 未配置">
        <template #extra>
          <n-button size="small" @click="openSettings">
            配置 Grafana
          </n-button>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon, NEmpty } from 'naive-ui'
import { ExternalLinkOutline } from '@vicons/ionicons5'

const props = defineProps<{
  title?: string
  dashboardUid: string
  panelId?: number
  width?: string | number
  height?: string | number
  deviceId?: string
}>()

const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000'

const embeddedUrl = computed(() => {
  const base = `${grafanaUrl}/d-solo/${props.dashboardUid}`
  const params = new URLSearchParams()
  if (props.panelId) params.append('panelId', String(props.panelId))
  if (props.deviceId) params.append('var-device', props.deviceId)
  params.append('from', 'now-1h')
  params.append('to', 'now')
  return `${base}?${params.toString()}`
})

const openGrafana = () => {
  window.open(`${grafanaUrl}/d/${props.dashboardUid}`, '_blank')
}

const openSettings = () => {
  // 打开配置对话框
}
</script>

<style scoped>
.grafana-panel {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.panel-content iframe {
  border-radius: 4px;
}
</style>
```

**Step 2: 提交**

```bash
git add frontend/src/components/GrafanaPanel.vue
git commit -m "feat(frontend): 添加 Grafana 面板组件"
```

---

### Task 12: 创建 Prometheus 直接查询 Hook

**Files:**
- Create: `frontend/src/composables/usePrometheus.ts`

**Step 1: 创建 Prometheus 查询 Hook**

```typescript
/**
 * Prometheus 数据查询 Hook
 * 用于直接查询 Prometheus API 获取监控数据
 */

import { ref } from 'vue'
import axios from 'axios'

const PROMETHEUS_URL = import.meta.env.VITE_PROMETHEUS_URL || 'http://localhost:9090'

export interface MetricPoint {
  timestamp: number
  value: number
}

export interface MetricSeries {
  metric: string
  points: MetricPoint[]
}

export function usePrometheus() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * 查询单个指标
   */
  async function queryMetric(
    query: string,
    time?: string
  ): Promise<MetricSeries[]> {
    loading.value = true
    error.value = null

    try {
      const params: Record<string, string> = { query }
      if (time) params.time = time

      const response = await axios.get(
        `${PROMETHEUS_URL}/api/v1/query`,
        { params }
      )

      if (response.data.status !== 'success') {
        throw new Error(response.data.error || 'Query failed')
      }

      return response.data.data.result.map((item: any) => ({
        metric: item.metric.__name__ || '',
        points: item.values.map(([ts, val]: [number, string]) => ({
          timestamp: ts * 1000,
          value: parseFloat(val)
        }))
      }))
    } catch (e: any) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 查询指标范围数据
   */
  async function queryRange(
    query: string,
    start: number,
    end: number,
    step = '15s'
  ): Promise<MetricSeries[]> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(
        `${PROMETHEUS_URL}/api/v1/query_range`,
        {
          params: { query, start, end, step }
        }
      )

      if (response.data.status !== 'success') {
        throw new Error(response.data.error || 'Query failed')
      }

      return response.data.data.result.map((item: any) => ({
        metric: item.metric.__name__ || '',
        points: item.values.map(([ts, val]: [number, string]) => ({
          timestamp: ts * 1000,
          value: parseFloat(val)
        }))
      }))
    } catch (e: any) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取 CPU 使用率
   */
  async function getCpuPercent(deviceId: string, minutes = 60) {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    const query = `windows_cpu_percent{instance="${deviceId}"}`
    return queryRange(query, start, end)
  }

  /**
   * 获取内存使用率
   */
  async function getMemoryPercent(deviceId: string, minutes = 60) {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    const query = `windows_memory_percent{instance="${deviceId}"}`
    return queryRange(query, start, end)
  }

  /**
   * 获取 GPU 指标
   */
  async function getGpuMetrics(deviceId: string, minutes = 60) {
    const end = Date.now() / 1000
    const start = end - minutes * 60
    
    const [utilization, temperature] = await Promise.all([
      queryRange(`windows_gpu_percent{instance="${deviceId}"}`, start, end),
      queryRange(`windows_gpu_temperature_celsius{instance="${deviceId}"}`, start, end)
    ])

    return { utilization, temperature }
  }

  return {
    loading,
    error,
    queryMetric,
    queryRange,
    getCpuPercent,
    getMemoryPercent,
    getGpuMetrics
  }
}
```

**Step 2: 提交**

```bash
git add frontend/src/composables/usePrometheus.ts
git commit -m "feat(frontend): 添加 Prometheus 查询 Hook"
```

---

### Task 13: 创建 Prometheus 监控页面

**Files:**
- Create: `frontend/src/views/PrometheusPerformance.vue`

**Step 1: 创建基于 Prometheus 的监控页面**

```vue
<template>
  <div class="prometheus-performance">
    <header class="page-header">
      <div class="header-left">
        <h1>性能监控 (Prometheus)</h1>
        <span class="subtitle">实时硬件性能监控</span>
      </div>
      <div class="header-right">
        <n-select
          v-model:value="selectedDevice"
          :options="deviceOptions"
          placeholder="选择设备"
          style="width: 200px"
        />
        <n-button type="primary" @click="refreshData">
          <template #icon>
            <n-icon><RefreshOutline /></n-icon>
          </template>
          刷新
        </n-button>
      </div>
    </header>

    <!-- 快速概览 -->
    <section class="quick-stats">
      <n-grid :cols="4" :x-gap="16">
        <n-gi>
          <div class="stat-card">
            <div class="stat-label">CPU 使用率</div>
            <div class="stat-value">{{ currentMetrics.cpu }}%</div>
            <div class="stat-chart">
              <GrafanaPanel
                dashboard-uid="windows-exporter"
                panel-id="cpu"
                :height="100"
              />
            </div>
          </div>
        </n-gi>
        <n-gi>
          <div class="stat-card">
            <div class="stat-label">内存使用率</div>
            <div class="stat-value">{{ currentMetrics.memory }}%</div>
            <div class="stat-chart">
              <GrafanaPanel
                dashboard-uid="windows-exporter"
                panel-id="memory"
                :height="100"
              />
            </div>
          </div>
        </n-gi>
        <n-gi>
          <div class="stat-card">
            <div class="stat-label">GPU 使用率</div>
            <div class="stat-value">{{ currentMetrics.gpu || 'N/A' }}%</div>
          </div>
        </n-gi>
        <n-gi>
          <div class="stat-card">
            <div class="stat-label">GPU 温度</div>
            <div class="stat-value">{{ currentMetrics.gpuTemp || 'N/A' }}°C</div>
          </div>
        </n-gi>
      </n-grid>
    </section>

    <!-- Grafana 嵌入面板 -->
    <section class="grafana-section">
      <h2>Grafana 监控面板</h2>
      <GrafanaPanel
        dashboard-uid="windows-exporter"
        :device-id="selectedDevice"
        :width="'100%'"
        :height="400"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { NButton, NIcon, NSelect, NGrid, NGi } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { usePrometheus } from '@/composables/usePrometheus'
import GrafanaPanel from '@/components/GrafanaPanel.vue'

const selectedDevice = ref<string | null>(null)
const deviceOptions = ref<{ label: string; value: string }[]>([])
const currentMetrics = ref({
  cpu: 0,
  memory: 0,
  gpu: null as number | null,
  gpuTemp: null as number | null
})

const { getCpuPercent, getMemoryPercent, getGpuMetrics, loading } = usePrometheus()

const loadDevices = async () => {
  // 从 API 加载设备列表
  const { data } = await api.get('/devices')
  deviceOptions.value = data.items.map((d: any) => ({
    label: d.device_name,
    value: d.hostname  // 使用 hostname 作为 Prometheus instance
  }))
  
  if (deviceOptions.value.length > 0) {
    selectedDevice.value = deviceOptions.value[0].value
  }
}

const refreshData = async () => {
  if (!selectedDevice.value) return
  
  const [cpu, memory, gpu] = await Promise.all([
    getCpuPercent(selectedDevice.value, 5),
    getMemoryPercent(selectedDevice.value, 5),
    getGpuMetrics(selectedDevice.value, 5)
  ])
  
  // 更新当前值
  if (cpu.length > 0 && cpu[0].points.length > 0) {
    currentMetrics.value.cpu = cpu[0].points[cpu[0].points.length - 1].value
  }
  
  if (memory.length > 0 && memory[0].points.length > 0) {
    currentMetrics.value.memory = memory[0].points[memory[0].points.length - 1].value
  }
  
  if (gpu.utilization.length > 0 && gpu.utilization[0].points.length > 0) {
    currentMetrics.value.gpu = gpu.utilization[0].points[gpu.utilization[0].points.length - 1].value
  }
  
  if (gpu.temperature.length > 0 && gpu.temperature[0].points.length > 0) {
    currentMetrics.value.gpuTemp = gpu.temperature[0].points[gpu.temperature[0].points.length - 1].value
  }
}

watch(selectedDevice, () => {
  refreshData()
})

onMounted(() => {
  loadDevices()
})
</script>
```

**Step 2: 提交**

```bash
git add frontend/src/views/PrometheusPerformance.vue
git commit -m "feat(frontend): 添加 Prometheus 监控页面"
```

---

## Phase 5: 文档与部署

### Task 14: 创建 Prometheus 部署文档

**Files:**
- Create: `docs/prometheus-deployment.md`

**Step 1: 创建部署文档**

```markdown
# Prometheus 部署指南

## 前提条件

- Docker 和 Docker Compose 已安装
- Windows Server 2016+ 或 Windows 10/11
- 至少 4GB RAM 可用

## 快速开始

### 1. 启动 Prometheus 生态

```bash
cd deploy
docker-compose -f docker-compose.prometheus.yml up -d
```

### 2. 在目标机器安装 windows_exporter

```batch
# 以管理员身份运行
cd deploy/windows_exporter
deploy.bat
```

### 3. 访问服务

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin123)
- windows_exporter: http://localhost:9182/metrics

## 架构说明

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ windows_   │────▶│ Prometheus  │────▶│   Grafana   │
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

## 指标列表

| 指标名称 | 类型 | 说明 |
|----------|------|------|
| windows_cpu_percent | Gauge | CPU 使用率 (%) |
| windows_memory_percent | Gauge | 内存使用率 (%) |
| windows_disk_read_bytes | Counter | 磁盘读取字节数 |
| windows_disk_write_bytes | Counter | 磁盘写入字节数 |
| windows_network_sent_bytes | Counter | 网络发送字节数 |
| windows_network_recv_bytes | Counter | 网络接收字节数 |
| windows_gpu_percent | Gauge | GPU 使用率 (%) |
| windows_gpu_temperature_celsius | Gauge | GPU 温度 (°C) |
| windows_cpu_temperature_celsius | Gauge | CPU 温度 (°C) |

## 告警规则

参考 `deploy/prometheus/alert.rules.yml`

## 故障排除

### windows_exporter 无法启动

1. 检查是否有其他服务占用端口 9182
2. 以管理员身份运行服务安装命令
3. 查看日志: `eventvwr` → Windows 日志 → 应用程序

### Prometheus 无法抓取

1. 检查防火墙设置
2. 验证目标机器端口可访问: `curl http://target:9182/metrics`
3. 检查 Prometheus 日志

### Grafana 仪表盘空白

1. 确认 Prometheus 数据源已配置
2. 检查查询的指标名称是否正确
3. 验证时间范围设置
```

**Step 2: 提交**

```bash
git add docs/prometheus-deployment.md
git commit -m "docs: 添加 Prometheus 部署文档"
```

---

### Task 15: 创建一键部署脚本

**Files:**
- Create: `deploy/start-prometheus.sh`
- Create: `deploy/stop-prometheus.sh`

**Step 1: 创建启动脚本**

```bash
#!/bin/bash

set -e

echo "Starting Prometheus monitoring stack..."

# 创建网络
docker network create monitoring 2>/dev/null || true

# 启动服务
docker-compose -f docker-compose.prometheus.yml up -d

echo ""
echo "Services started:"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - AlertManager: http://localhost:9093"
echo ""
echo "Next steps:"
echo "  1. Install windows_exporter on target machines"
echo "  2. Access Grafana to view dashboards"
```

**Step 2: 创建停止脚本**

```bash
#!/bin/bash

set -e

echo "Stopping Prometheus monitoring stack..."

docker-compose -f docker-compose.prometheus.yml down

echo "Services stopped."
```

**Step 3: 提交**

```bash
git add deploy/start-prometheus.sh deploy/stop-prometheus.sh
chmod +x deploy/start-prometheus.sh deploy/stop-prometheus.sh
git commit -m "feat(deploy): 添加 Prometheus 一键启停脚本"
```

---

## 执行检查清单

完成所有 Task 后，确认以下内容：

- [ ] Prometheus Server 正常运行在 9090 端口
- [ ] Grafana 正常运行在 3000 端口
- [ ] windows_exporter 可在 9182 端口访问
- [ ] Grafana 中已配置 Prometheus 数据源
- [ ] Windows Exporter Dashboard 已导入
- [ ] 后端 API 可查询 Prometheus 数据
- [ ] 前端页面可显示 Grafana 面板
- [ ] 文档完整且可参考

---

## 回滚计划

如果需要回滚到原有架构：

1. 删除 Prometheus 相关容器
2. 恢复原有 Agent (Push 模式)
3. 恢复原有后端 API
4. 恢复原有前端页面

```bash
# 停止并删除 Prometheus 服务
docker-compose -f docker-compose.prometheus.yml down -v

# 切换回 main 分支
git checkout main
```

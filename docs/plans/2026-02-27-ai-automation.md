# AI自动化功能实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现AI自动化功能，支持3D软件性能测试和AI分析

**Architecture:** 采用分层架构 - 数据采集层(Agent) + 控制层(后端API) + AI分析层(LLM) + 可视化层(前端)

**Tech Stack:** FastAPI, SQLite, Vue 3, WebSocket, LLM Providers (MiniMax/DeepSeek/硅基流动)

---

## 实施范围 (MVP版本)

根据文档MVP定义：
- 支持软件: Blender (开源, API完善)
- 测试场景: 场景加载、简单渲染
- 硬件采集: CPU/GPU/内存/磁盘
- LLM分析: 基础瓶颈识别 + 升级建议

---

## Task 1: 创建数据库模型

**Files:**
- Modify: `backend/app/models/sqlite.py` - 添加新表
- Create: `backend/app/schemas/performance.py` - Pydantic schemas
- Test: 运行 `python -c "from app.models.sqlite import Base; print('OK')"`

**Step 1: 添加新模型到 sqlite.py**

在文件末尾添加:

```python
class PerformanceMetric(Base):
    """性能指标记录"""
    __tablename__ = "performance_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # 基础指标
    cpu_usage = Column(Float, nullable=True)
    cpu_temp = Column(Float, nullable=True)
    gpu_usage = Column(Float, nullable=True)
    gpu_temp = Column(Float, nullable=True)
    gpu_vram_used = Column(Integer, nullable=True)
    ram_usage = Column(Float, nullable=True)
    ram_total_gb = Column(Float, nullable=True)
    
    # 磁盘
    disk_read_speed = Column(Integer, nullable=True)
    disk_write_speed = Column(Integer, nullable=True)
    
    # 网络
    network_upload_speed = Column(Integer, nullable=True)
    network_download_speed = Column(Integer, nullable=True)
    
    device = relationship("Device", backref="performance_metrics")


class SoftwareBenchmark(Base):
    """软件性能测试结果"""
    __tablename__ = "software_benchmarks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    software_name = Column(String(100), nullable=False)
    
    # 测试结果
    startup_time = Column(Float, nullable=True)  # 启动时间(秒)
    memory_usage_mb = Column(Integer, nullable=True)
    cpu_usage = Column(Float, nullable=True)
    gpu_usage = Column(Float, nullable=True)
    
    test_result = Column(Text, nullable=True)  # JSON详细结果
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    device = relationship("Device", backref="software_benchmarks")


class ControlCommand(Base):
    """控制命令记录"""
    __tablename__ = "control_commands"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    
    command = Column(String(50), nullable=False)  # launch_software, close_software, run_benchmark等
    params = Column(Text, nullable=True)  # JSON参数
    
    status = Column(String(20), default="pending", index=True)  # pending/running/completed/failed
    result = Column(Text, nullable=True)  # JSON结果
    
    issued_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    issued_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    device = relationship("Device", backref="control_commands")


class PerformanceAlert(Base):
    """性能告警"""
    __tablename__ = "performance_alerts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    
    alert_type = Column(String(50), nullable=False)  # offline/high_temp/low_performance
    severity = Column(String(20), nullable=False)  # info/warning/error/critical
    
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    device = relationship("Device", backref="performance_alerts")
```

**Step 2: 创建Pydantic schemas**

创建 `backend/app/schemas/performance.py`:

```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PerformanceMetricBase(BaseModel):
    cpu_usage: Optional[float] = None
    cpu_temp: Optional[float] = None
    gpu_usage: Optional[float] = None
    gpu_temp: Optional[float] = None
    gpu_vram_used: Optional[int] = None
    ram_usage: Optional[float] = None
    ram_total_gb: Optional[float] = None
    disk_read_speed: Optional[int] = None
    disk_write_speed: Optional[int] = None


class PerformanceMetricCreate(PerformanceMetricBase):
    device_id: str


class PerformanceMetricResponse(PerformanceMetricBase):
    id: str
    device_id: str
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class SoftwareBenchmarkBase(BaseModel):
    software_name: str
    startup_time: Optional[float] = None
    memory_usage_mb: Optional[int] = None
    cpu_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    test_result: Optional[dict] = None


class SoftwareBenchmarkCreate(SoftwareBenchmarkBase):
    device_id: str


class SoftwareBenchmarkResponse(SoftwareBenchmarkBase):
    id: str
    device_id: str
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class ControlCommandCreate(BaseModel):
    device_id: str
    command: str
    params: Optional[dict] = None


class ControlCommandResponse(BaseModel):
    id: str
    device_id: str
    command: str
    params: Optional[dict] = None
    status: str
    result: Optional[dict] = None
    issued_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PerformanceAlertCreate(BaseModel):
    device_id: str
    alert_type: str
    severity: str
    title: str
    message: Optional[str] = None


class PerformanceAlertResponse(BaseModel):
    id: str
    device_id: str
    alert_type: str
    severity: str
    title: str
    message: Optional[str] = None
    is_resolved: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
```

**Step 3: 验证模型**

Run: `cd backend && python -c "from app.models.sqlite import PerformanceMetric, SoftwareBenchmark, ControlCommand, PerformanceAlert; print('Models OK')"`
Expected: 输出 "Models OK"

**Step 4: 提交**
```bash
git add backend/app/models/sqlite.py backend/app/schemas/performance.py
git commit -m "feat: add performance models and schemas"
```

---

## Task 2: 创建性能指标API

**Files:**
- Create: `backend/app/api/performance.py`
- Modify: `backend/app/api/__init__.py` - 注册路由

**Step 1: 创建API文件**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db_sync
from app.models.sqlite import Device, PerformanceMetric, SoftwareBenchmark, PerformanceAlert
from app.schemas.performance import (
    PerformanceMetricCreate, PerformanceMetricResponse,
    SoftwareBenchmarkCreate, SoftwareBenchmarkResponse,
    PerformanceAlertCreate, PerformanceAlertResponse
)

router = APIRouter(prefix="/performance", tags=["Performance"])


# ====== 性能指标 API ======

@router.get("/metrics/{device_id}", response_model=List[PerformanceMetricResponse])
def get_device_metrics(
    device_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db_sync)
):
    """获取设备性能指标历史"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    query = select(PerformanceMetric).where(
        PerformanceMetric.device_id == device_id,
        PerformanceMetric.recorded_at >= cutoff
    ).order_by(desc(PerformanceMetric.recorded_at))
    
    result = db.execute(query)
    return result.scalars().all()


@router.get("/metrics/{device_id}/latest")
def get_latest_metrics(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备最新性能指标"""
    query = select(PerformanceMetric).where(
        PerformanceMetric.device_id == device_id
    ).order_by(desc(PerformanceMetric.recorded_at)).limit(1)
    
    result = db.execute(query)
    metric = result.scalar_one_or_none()
    
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics found")
    
    return {
        "cpu_usage": metric.cpu_usage,
        "cpu_temp": metric.cpu_temp,
        "gpu_usage": metric.gpu_usage,
        "gpu_temp": metric.gpu_temp,
        "gpu_vram_used": metric.gpu_vram_used,
        "ram_usage": metric.ram_usage,
        "ram_total_gb": metric.ram_total_gb,
        "recorded_at": metric.recorded_at.isoformat() if metric.recorded_at else None
    }


@router.post("/metrics", response_model=PerformanceMetricResponse)
def create_metric(data: PerformanceMetricCreate, db: Session = Depends(get_db_sync)):
    """记录性能指标 (Agent调用)"""
    metric = PerformanceMetric(**data.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


# ====== 软件基准测试 API ======

@router.get("/benchmarks/{device_id}", response_model=List[SoftwareBenchmarkResponse])
def get_device_benchmarks(
    device_id: str,
    software_name: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_sync)
):
    """获取设备软件基准测试历史"""
    query = select(SoftwareBenchmark).where(
        SoftwareBenchmark.device_id == device_id
    )
    
    if software_name:
        query = query.where(SoftwareBenchmark.software_name == software_name)
    
    query = query.order_by(desc(SoftwareBenchmark.recorded_at)).limit(limit)
    
    result = db.execute(query)
    return result.scalars().all()


@router.post("/benchmarks", response_model=SoftwareBenchmarkResponse)
def create_benchmark(data: SoftwareBenchmarkCreate, db: Session = Depends(get_db_sync)):
    """记录软件基准测试结果 (Agent调用)"""
    benchmark_data = data.model_dump()
    if benchmark_data.get('test_result') and isinstance(benchmark_data['test_result'], dict):
        import json
        benchmark_data['test_result'] = json.dumps(benchmark_data['test_result'])
    
    benchmark = SoftwareBenchmark(**benchmark_data)
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)
    return benchmark


# ====== 告警 API ======

@router.get("/alerts", response_model=List[PerformanceAlertResponse])
def get_alerts(
    device_id: Optional[str] = None,
    is_resolved: Optional[bool] = False,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_sync)
):
    """获取告警列表"""
    query = select(PerformanceAlert)
    
    if device_id:
        query = query.where(PerformanceAlert.device_id == device_id)
    if is_resolved is not None:
        query = query.where(PerformanceAlert.is_resolved == is_resolved)
    
    query = query.order_by(desc(PerformanceAlert.created_at)).limit(limit)
    
    result = db.execute(query)
    return result.scalars().all()


@router.post("/alerts", response_model=PerformanceAlertResponse)
def create_alert(data: PerformanceAlertCreate, db: Session = Depends(get_db_sync)):
    """创建告警"""
    alert = PerformanceAlert(**data.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db_sync)):
    """标记告警已处理"""
    result = db.execute(select(PerformanceAlert).where(PerformanceAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    db.commit()
    
    return {"status": "resolved", "alert_id": alert_id}
```

**Step 2: 注册路由**

在 `backend/app/api/__init__.py` 添加:
```python
from app.api.performance import router as performance_router
```

并注册:
```python
app.include_router(performance_router)
```

**Step 3: 测试API**

Run: `cd backend && python -c "from app.api.performance import router; print('API OK')"`
Expected: 输出 "API OK"

**Step 4: 提交**
```bash
git add backend/app/api/performance.py backend/app/api/__init__.py
git commit -m "feat: add performance metrics API"
```

---

## Task 3: 创建LLM分析服务

**Files:**
- Create: `backend/app/services/ai_analysis_service.py`
- Modify: `backend/app/core/config.py` - 添加LLM配置

**Step 1: 创建AI分析服务**

```python
import json
from typing import Optional, Dict, Any
from app.core.config import settings


ANALYSIS_PROMPT = """
你是硬件性能分析专家。请分析以下测试数据并给出专业建议。

## 测试环境
- 测试软件: {software_name}
- 测试场景: {test_scenario}
- 测试时间: {test_duration}s

## 硬件配置
- CPU: {cpu_model}
- GPU: {gpu_model}
- 显存: {vram_gb}GB
- 内存: {ram_gb}GB

## 性能数据
{performance_data}

## 标杆数据（参考）
{benchmark_data}

请分析以下内容：
1. 瓶颈识别：主要性能瓶颈在哪里？
2. 量化评估：与标杆机相比差距多少？
3. 升级建议：优先升级哪个硬件？
4. ROI分析：升级后的预期改善

## 输出格式
请以 JSON 格式输出：
{{
  "bottleneck": "CPU/GPU/MEMORY/DISK",
  "score_loss_percent": 25,
  "upgrade_priority": ["GPU", "RAM"],
  "estimated_improvement": "30%",
  "reasoning": "详细分析理由"
}}
"""


class AIAnalysisService:
    """AI分析服务"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
    
    async def analyze_benchmark(
        self,
        software_name: str,
        test_scenario: str,
        hardware_info: Dict[str, Any],
        benchmark_data: Dict[str, Any],
        reference_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析基准测试结果"""
        
        # 构建prompt
        prompt = ANALYSIS_PROMPT.format(
            software_name=software_name,
            test_scenario=test_scenario,
            test_duration=benchmark_data.get('duration', 0),
            cpu_model=hardware_info.get('cpu_model', 'Unknown'),
            gpu_model=hardware_info.get('gpu_model', 'Unknown'),
            vram_gb=hardware_info.get('gpu_vram_gb', 0),
            ram_gb=hardware_info.get('ram_gb', 0),
            performance_data=json.dumps(benchmark_data, indent=2),
            benchmark_data=json.dumps(reference_data or {}, indent=2)
        )
        
        # 调用LLM
        try:
            from app.services.llm_service import llm_service
            response = await llm_service.chat([
                {"role": "user", "content": prompt}
            ])
            
            # 解析JSON响应
            return self._parse_llm_response(response)
        except Exception as e:
            return {
                "error": str(e),
                "bottleneck": "UNKNOWN",
                "upgrade_priority": [],
                "reasoning": "AI分析失败"
            }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "bottleneck": "UNKNOWN",
            "upgrade_priority": [],
            "reasoning": response[:500]
        }


# 导出单例
ai_analysis_service = AIAnalysisService()
```

**Step 2: 更新配置**

在 `backend/app/core/config.py` 添加:

```python
# LLM Configuration
LLM_PROVIDER: str = Field(default="minimax", env="LLM_PROVIDER")
LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
LLM_MODEL: str = Field(default="MiniMax-M2.5-highspeed", env="LLM_MODEL")
LLM_TIMEOUT: int = Field(default=60, env="LLM_TIMEOUT")
```

**Step 3: 测试**

Run: `cd backend && python -c "from app.services.ai_analysis_service import ai_analysis_service; print('Service OK')"`
Expected: 输出 "Service OK"

**Step 4: 提交**
```bash
git add backend/app/services/ai_analysis_service.py backend/app/core/config.py
git commit -m "feat: add AI analysis service"
```

---

## Task 4: 创建AI分析API

**Files:**
- Create: `backend/app/api/ai_analysis.py`

**Step 1: 创建API**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db_sync
from app.models.sqlite import Device, SoftwareBenchmark
from app.services.ai_analysis_service import ai_analysis_service

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post("/analyze/benchmark/{benchmark_id}")
async def analyze_benchmark(
    benchmark_id: str,
    db: Session = Depends(get_db_sync)
):
    """AI分析基准测试结果"""
    
    # 获取基准测试数据
    result = db.execute(select(SoftwareBenchmark).where(SoftwareBenchmark.id == benchmark_id))
    benchmark = result.scalar_one_or_none()
    
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    
    # 获取设备硬件信息
    device_result = db.execute(select(Device).where(Device.id == benchmark.device_id))
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 准备硬件信息
    hardware_info = {
        "cpu_model": device.cpu_model or "Unknown",
        "gpu_model": device.gpu_model or "Unknown",
        "gpu_vram_gb": (device.gpu_vram_mb or 0) / 1024,
        "ram_gb": device.ram_total_gb or 0
    }
    
    # 准备基准测试数据
    benchmark_data = {
        "startup_time": benchmark.startup_time,
        "memory_usage_mb": benchmark.memory_usage_mb,
        "cpu_usage": benchmark.cpu_usage,
        "gpu_usage": benchmark.gpu_usage
    }
    
    if benchmark.test_result:
        import json
        try:
            benchmark_data.update(json.loads(benchmark.test_result))
        except:
            pass
    
    # 调用AI分析
    analysis = await ai_analysis_service.analyze_benchmark(
        software_name=benchmark.software_name,
        test_scenario="general",
        hardware_info=hardware_info,
        benchmark_data=benchmark_data
    )
    
    return {
        "benchmark_id": benchmark_id,
        "analysis": analysis
    }


@router.post("/analyze/device/{device_id}")
async def analyze_device(
    device_id: str,
    db: Session = Depends(get_db_sync)
):
    """AI分析设备整体性能"""
    
    # 获取设备信息
    device_result = db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 获取最近基准测试
    benchmarks_result = db.execute(
        select(SoftwareBenchmark).where(
            SoftwareBenchmark.device_id == device_id
        ).order_by(SoftwareBenchmark.recorded_at.desc()).limit(10)
    )
    benchmarks = benchmarks_result.scalars().all()
    
    hardware_info = {
        "cpu_model": device.cpu_model or "Unknown",
        "cpu_cores": device.cpu_cores,
        "gpu_model": device.gpu_model or "Unknown",
        "gpu_vram_gb": (device.gpu_vram_mb or 0) / 1024,
        "ram_gb": device.ram_total_gb or 0
    }
    
    # 汇总基准测试数据
    benchmark_summary = {}
    for b in benchmarks:
        if b.software_name not in benchmark_summary:
            benchmark_summary[b.software_name] = {
                "startup_time": b.startup_time,
                "cpu_usage": b.cpu_usage,
                "gpu_usage": b.gpu_usage
            }
    
    # 调用AI分析
    analysis = await ai_analysis_service.analyze_benchmark(
        software_name="综合分析",
        test_scenario="设备整体评估",
        hardware_info=hardware_info,
        benchmark_data=benchmark_summary
    )
    
    return {
        "device_id": device_id,
        "hardware": hardware_info,
        "recent_benchmarks": len(benchmarks),
        "analysis": analysis
    }
```

**Step 2: 注册路由**

在 `backend/app/api/__init__.py` 添加AI分析路由

**Step 3: 测试**

Run: `cd backend && python -c "from app.api.ai_analysis import router; print('AI API OK')"`

**Step 4: 提交**
```bash
git add backend/app/api/ai_analysis.py
git commit -m "feat: add AI analysis API"
```

---

## Task 5: 前端页面 - 性能监控

**Files:**
- Create: `frontend/src/views/Performance/PerformanceDashboard.vue`
- Modify: `frontend/src/App.vue` - 添加菜单项
- Modify: `frontend/src/router/index.ts` - 添加路由

**Step 1: 创建性能监控页面**

```vue
<template>
  <div class="performance-dashboard">
    <div class="page-header">
      <h1>性能监控</h1>
    </div>
    
    <!-- 实时指标 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16">
      <n-gi v-for="metric in realtimeMetrics" :key="metric.key">
        <n-card>
          <div class="metric-card">
            <n-icon :size="32" :color="metric.color">
              <component :is="metric.icon" />
            </n-icon>
            <div class="metric-info">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
    
    <!-- 设备列表 -->
    <n-card title="在线设备" style="margin-top: 16px">
      <n-data-table
        :columns="columns"
        :data="devices"
        :loading="loading"
      />
    </n-card>
    
    <!-- 告警列表 -->
    <n-card title="最近告警" style="margin-top: 16px">
      <n-list>
        <n-list-item v-for="alert in alerts" :key="alert.id">
          <n-tag :type="getAlertType(alert.severity)">{{ alert.severity }}</n-tag>
          <span style="margin-left: 8px">{{ alert.title }}</span>
          <span style="float: right; color: #999">{{ formatTime(alert.created_at) }}</span>
        </n-list-item>
      </n-list>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NCard, NGrid, NGi, NIcon, NDataTable, NTag, NList, NListItem } from 'naive-ui'
import { Cpu, MemoryStick, Display, HardDrive } from '@vicons/ionicons5'

const devices = ref([])
const alerts = ref([])
const loading = ref(false)

const realtimeMetrics = ref([
  { key: 'cpu', label: 'CPU平均使用率', value: '45%', color: '#0ea5e9', icon: Cpu },
  { key: 'gpu', label: 'GPU平均使用率', value: '62%', color: '#8b5cf6', icon: Display },
  { key: 'ram', label: '内存平均使用率', value: '58%', color: '#10b981', icon: MemoryStick },
  { key: 'disk', label: '磁盘平均使用率', value: '35%', color: '#f59e0b', icon: HardDrive }
])

const columns = [
  { title: '设备名称', key: 'device_name' },
  { title: 'IP地址', key: 'ip_address' },
  { title: '部门', key: 'department' },
  { title: '状态', key: 'status' },
  { title: '最后活跃', key: 'last_seen_at' }
]

const getAlertType = (severity: string) => {
  const map: Record<string, 'error' | 'warning' | 'info' | 'success'> = {
    critical: 'error',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return map[severity] || 'info'
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(async () => {
  loading.value = true
  // TODO: 加载数据
  loading.value = false
})
</script>

<style scoped>
.performance-dashboard {
  padding: 20px;
}
.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
}
.metric-value {
  font-size: 24px;
  font-weight: 600;
}
.metric-label {
  color: #666;
  font-size: 14px;
}
</style>
```

**Step 2: 添加路由**

在路由配置中添加:
```typescript
{
  path: '/performance',
  name: 'PerformanceDashboard',
  component: () => import('@/views/Performance/PerformanceDashboard.vue')
}
```

**Step 3: 添加菜单项**

在 `frontend/src/App.vue` 菜单中添加 "性能监控"

**Step 4: 提交**
```bash
git add frontend/src/views/Performance/
git commit -m "feat: add performance dashboard page"
```

---

## Task 6: 创建Agent示例脚本

**Files:**
- Create: `backend/agent/hardware_monitor.py` - Agent示例脚本

**Step 1: 创建硬件监控脚本**

```python
"""
硬件性能监控Agent示例
部署到员工电脑，定期采集硬件指标上报到服务端
"""
import psutil
import time
import requests
import json
from datetime import datetime


class HardwareMonitor:
    def __init__(self, device_id: str, api_base: str):
        self.device_id = device_id
        self.api_base = api_base.rstrip('/')
        self.interval = 60  # 采集间隔(秒)
    
    def get_metrics(self) -> dict:
        """采集硬件指标"""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存
        mem = psutil.virtual_memory()
        
        # GPU (需要nvidia-smi或pynvml)
        gpu_data = self._get_gpu_metrics()
        
        # 磁盘
        disk = psutil.disk_usage('/')
        
        return {
            "device_id": self.device_id,
            "cpu_usage": cpu_percent,
            "cpu_temp": self._get_cpu_temp(),
            "gpu_usage": gpu_data.get("usage"),
            "gpu_temp": gpu_data.get("temp"),
            "gpu_vram_used": gpu_data.get("vram_used"),
            "ram_usage": mem.percent,
            "ram_total_gb": mem.total / (1024**3),
            "disk_read_speed": 0,  # 需要更复杂的计算
            "disk_write_speed": 0
        }
    
    def _get_cpu_temp(self) -> float:
        """获取CPU温度"""
        try:
            # Windows: 使用wmi
            import wmi
            w = wmi.WMI()
            for temp in w.Win32_TemperatureProbe():
                if temp.CurrentReading:
                    return temp.CurrentReading / 10.0
        except:
            pass
        return None
    
    def _get_gpu_metrics(self) -> dict:
        """获取GPU指标"""
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            return {
                "usage": util.gpu,
                "vram_used": info.used // (1024**2),
                "temp": 0  # 需要额外调用
            }
        except:
            pass
        
        return {"usage": None, "vram_used": None, "temp": None}
    
    def report_metrics(self, metrics: dict):
        """上报指标到服务端"""
        url = f"{self.api_base}/api/performance/metrics"
        try:
            response = requests.post(url, json=metrics, timeout=10)
            return response.ok
        except Exception as e:
            print(f"Failed to report metrics: {e}")
            return False
    
    def run(self):
        """持续采集和上报"""
        print(f"Hardware monitor started for device: {self.device_id}")
        
        while True:
            try:
                metrics = self.get_metrics()
                print(f"Metrics: {metrics}")
                
                self.report_metrics(metrics)
                time.sleep(self.interval)
            except KeyboardInterrupt:
                print("Monitor stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    import uuid
    
    # 方式1: 使用设备ID
    device_id = "your-device-id"
    
    # 方式2: 自动注册获取ID
    # device_id = register_device("hostname", "mac-address")
    
    monitor = HardwareMonitor(
        device_id=device_id,
        api_base="http://localhost:8000"
    )
    monitor.run()
```

**Step 2: 创建Blender测试脚本**

```python
"""
Blender自动化性能测试
"""
import bpy
import time
import json
import subprocess
import sys


class BlenderBenchmark:
    def __init__(self, blend_file: str = None):
        self.blend_file = blend_file
        self.results = {}
    
    def test_scene_load(self, filepath: str) -> dict:
        """测试场景加载时间"""
        start = time.time()
        
        # 加载场景
        bpy.ops.wm.open(filepath=filepath)
        
        load_time = time.time() - start
        
        return {
            "test": "scene_load",
            "duration": load_time,
            "filepath": filepath
        }
    
    def test_render(self, samples: int = 128) -> dict:
        """测试渲染性能"""
        # 设置渲染参数
        bpy.context.scene.cycles.samples = samples
        
        start = time.time()
        bpy.ops.render.render()
        render_time = time.time() - start
        
        return {
            "test": "render",
            "samples": samples,
            "duration": render_time
        }
    
    def run_full_benchmark(self) -> dict:
        """运行完整基准测试"""
        results = {
            "software": "Blender",
            "version": bpy.app.version_string,
            "timestamp": time.time(),
            "tests": []
        }
        
        # 场景加载测试
        if self.blend_file:
            load_result = self.test_scene_load(self.blend_file)
            results["tests"].append(load_result)
        
        # 渲染测试
        render_result = self.test_render()
        results["tests"].append(render_result)
        
        # 保存结果
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return results


if __name__ == "__main__":
    # Blender中运行
    benchmark = BlenderBenchmark()
    results = benchmark.run_full_benchmark()
    print(json.dumps(results, indent=2))
```

**Step 3: 提交**
```bash
git add backend/agent/
git commit -m "feat: add agent scripts for hardware monitoring and benchmarking"
```

---

## 执行选项

**Plan complete and saved to `docs/plans/2026-02-27-ai-automation.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

"""
Prometheus 监控 API 端点
用于从 Prometheus 获取硬件监控数据

Deprecated: 此 API 已废弃，请使用 /api/performance/* 端点
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.services.prometheus_service import prometheus_service

router = APIRouter(prefix="/prometheus", tags=["Prometheus (Deprecated)"])


# ==================== Response Models ====================


class PrometheusStatus(BaseModel):
    """Prometheus 连接状态"""

    available: bool
    url: str
    message: str


class InstanceMetrics(BaseModel):
    """实例指标"""

    instance: str
    timestamp: str
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_temperature: Optional[float] = None
    cpu_temperature: Optional[float] = None


class MetricHistoryPoint(BaseModel):
    """指标历史数据点"""

    timestamp: str
    value: float


class MetricHistory(BaseModel):
    """指标历史"""

    metric: str
    instance: str
    unit: str
    data: List[MetricHistoryPoint]


class GPUHistory(BaseModel):
    """GPU 历史"""

    utilization: List[MetricHistoryPoint]
    temperature: List[MetricHistoryPoint]


# ==================== Deprecated Warning ====================

DEPRECATION_WARNING = """
⚠️ 此 API 已废弃 (Deprecated)
请使用 /api/performance/* 端点获取性能数据。
Prometheus 将作为 /api/performance 的数据源。
"""


# ==================== Endpoints ====================


@router.get("/status", response_model=PrometheusStatus)
async def get_prometheus_status():
    """
    获取 Prometheus 连接状态

    Deprecated: 请使用 /api/performance/status
    """
    available = prometheus_service.is_available
    return PrometheusStatus(
        available=available,
        url=prometheus_service.prometheus_url,
        message="Prometheus is connected"
        if available
        else "Prometheus is not available",
    )


@router.get("/instances", response_model=List[str])
async def list_instances():
    """
    列出所有监控实例

    Deprecated: 请使用 /api/devices
    """
    instances = prometheus_service.list_instances()
    return instances


@router.get("/metrics/{instance}", response_model=InstanceMetrics)
async def get_instance_metrics(instance: str):
    """
    获取指定实例的最新指标

    Deprecated: 请使用 /api/performance/metrics/{device_id}
    """
    metrics = prometheus_service.get_latest_metrics(instance)
    return InstanceMetrics(**metrics)


@router.get("/metrics/{instance}/cpu/history", response_model=MetricHistory)
async def get_cpu_history(
    instance: str,
    minutes: int = Query(60, ge=5, le=1440, description="历史时间范围（分钟）"),
):
    """
    获取 CPU 使用率历史数据

    Deprecated: 请使用 /api/performance/metrics/{device_id}/trend?type=cpu
    """
    data = prometheus_service.get_cpu_history(instance, minutes)

    # 转换为标准格式
    result = []
    for item in data:
        for value in item.get("values", []):
            ts, val = value
            result.append(
                MetricHistoryPoint(
                    timestamp=datetime.fromtimestamp(ts).isoformat(), value=float(val)
                )
            )

    return MetricHistory(
        metric="cpu_percent", instance=instance, unit="percent", data=result
    )


@router.get("/metrics/{instance}/memory/history", response_model=MetricHistory)
async def get_memory_history(
    instance: str,
    minutes: int = Query(60, ge=5, le=1440, description="历史时间范围（分钟）"),
):
    """
    获取内存使用率历史数据

    Deprecated: 请使用 /api/performance/metrics/{device_id}/trend?type=memory
    """
    data = prometheus_service.get_memory_history(instance, minutes)

    result = []
    for item in data:
        for value in item.get("values", []):
            ts, val = value
            result.append(
                MetricHistoryPoint(
                    timestamp=datetime.fromtimestamp(ts).isoformat(), value=float(val)
                )
            )

    return MetricHistory(
        metric="memory_percent", instance=instance, unit="percent", data=result
    )


@router.get("/metrics/{instance}/gpu/history")
async def get_gpu_history(
    instance: str,
    minutes: int = Query(60, ge=5, le=1440, description="历史时间范围（分钟）"),
):
    """
    获取 GPU 指标历史数据

    Deprecated: 请使用 /api/performance/metrics/{device_id}/trend?type=gpu
    """
    data = prometheus_service.get_gpu_history(instance, minutes)

    utilization = []
    for item in data.get("utilization", []):
        for value in item.get("values", []):
            ts, val = value
            utilization.append(
                MetricHistoryPoint(
                    timestamp=datetime.fromtimestamp(ts).isoformat(), value=float(val)
                )
            )

    temperature = []
    for item in data.get("temperature", []):
        for value in item.get("values", []):
            ts, val = value
            temperature.append(
                MetricHistoryPoint(
                    timestamp=datetime.fromtimestamp(ts).isoformat(), value=float(val)
                )
            )

    return {"utilization": utilization, "temperature": temperature}


@router.get("/query")
async def query_prometheus(query: str = Query(..., description="PromQL 查询语句")):
    """
    直接执行 PromQL 查询

    Deprecated: 请使用 /api/performance/query
    """
    results = prometheus_service.query(query)
    return {"query": query, "result": results, "deprecated": True}


@router.get("/query/range")
async def query_prometheus_range(
    query: str = Query(..., description="PromQL 查询语句"),
    start_time: str = Query(..., description="开始时间 (ISO 格式)"),
    end_time: str = Query(..., description="结束时间 (ISO 格式)"),
    step: str = Query("15s", description="查询步长"),
):
    """
    执行范围 PromQL 查询

    Deprecated: 请使用 /api/performance/query/range
    """
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    results = prometheus_service.query_range(query, start, end, step)
    return {
        "query": query,
        "start": start_time,
        "end": end_time,
        "step": step,
        "result": results,
        "deprecated": True,
    }

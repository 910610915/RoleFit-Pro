from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db_sync
from app.models.sqlite import (
    PerformanceMetric,
    SoftwareBenchmark,
    ControlCommand,
    PerformanceAlert,
    AIAnalysisReport,
    Device,
)
from app.schemas.performance import (
    PerformanceMetricResponse,
    PerformanceMetricListResponse,
    MetricDataCreate,
    MetricsBatchCreate,
    SoftwareBenchmarkCreate,
    SoftwareBenchmarkResponse,
    SoftwareBenchmarkListResponse,
    ControlCommandCreate,
    ControlCommandResponse,
    ControlCommandListResponse,
    PerformanceAlertCreate,
    PerformanceAlertResponse,
    PerformanceAlertListResponse,
    AIAnalysisReportCreate,
    AIAnalysisReportResponse,
    AIAnalysisReportListResponse,
    BenchmarkStartRequest,
    BenchmarkResultRequest,
    AIAnalysisRequest,
    AIAnalysisResponse,
)

# 导入WebSocket推送服务
try:
    from app.services.websocket_service import push_metrics, push_alert

    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

    # 模拟函数
    async def push_metrics(device_id: str, metrics: dict):
        pass

    async def push_alert(alert: dict):
        pass


router = APIRouter(prefix="/performance", tags=["Performance"])


# ==================== Performance Metrics ====================


@router.post(
    "/metrics",
    response_model=PerformanceMetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(metric: MetricDataCreate, db: Session = Depends(get_db_sync)):
    """创建性能指标"""
    import json

    data = metric
    
    # 构建模型数据
    db_metric = PerformanceMetric(
        device_id=data.device_id,
        timestamp=data.timestamp if data.timestamp else datetime.utcnow(),
        cpu_percent=data.cpu_percent,
        cpu_temperature=data.cpu_temperature,
        cpu_power_watts=data.cpu_power_watts,
        cpu_frequency_mhz=data.cpu_frequency_mhz,
        gpu_percent=data.gpu_percent,
        gpu_temperature=data.gpu_temperature,
        gpu_power_watts=data.gpu_power_watts,
        gpu_frequency_mhz=data.gpu_frequency_mhz,
        gpu_memory_used_mb=data.gpu_memory_used_mb,
        gpu_memory_total_mb=data.gpu_memory_total_mb,
        memory_percent=data.memory_percent,
        memory_used_mb=data.memory_used_mb,
        memory_available_mb=data.memory_available_mb,
        disk_read_mbps=data.disk_read_mbps,
        disk_write_mbps=data.disk_write_mbps,
        disk_io_percent=data.disk_io_percent,
        network_sent_mbps=data.network_sent_mbps,
        network_recv_mbps=data.network_recv_mbps,
        process_count=data.process_count,
        top_processes=json.dumps(data.top_processes) if data.top_processes else None,
        raw_data=data.raw_data,
        disk_io_details=json.dumps(data.disk_io_details) if data.disk_io_details else None,
    )
    
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    # 手动构建响应字典，因为 top_processes 和 disk_io_details 在数据库中是 JSON 字符串
    metric_dict = {c.name: getattr(db_metric, c.name) for c in db_metric.__table__.columns}

    # 解析 JSON 字段
    if metric_dict.get("top_processes"):
        try:
            metric_dict["top_processes"] = json.loads(metric_dict["top_processes"])
        except:
            metric_dict["top_processes"] = None
            
    if metric_dict.get("disk_io_details"):
        try:
            metric_dict["disk_io_details"] = json.loads(metric_dict["disk_io_details"])
        except:
            metric_dict["disk_io_details"] = None
            
    return metric_dict


@router.post("/metrics/batch", status_code=status.HTTP_201_CREATED)
def create_metrics_batch(batch: MetricsBatchCreate, db: Session = Depends(get_db_sync)):
    """批量创建性能指标"""
    import json
    from datetime import datetime

    created_count = 0
    for metric_data in batch.metrics:
        metric_dict = metric_data.model_dump()

        # 设置 device_id
        metric_dict["device_id"] = batch.device_id

        # 处理时间戳（可能是字符串格式）
        timestamp_val = metric_dict.get("timestamp")
        if timestamp_val:
            if isinstance(timestamp_val, str):
                # 解析 ISO 格式字符串
                try:
                    metric_dict["timestamp"] = datetime.fromisoformat(
                        timestamp_val.replace("Z", "+00:00")
                    )
                except:
                    metric_dict["timestamp"] = datetime.utcnow()
        else:
            metric_dict["timestamp"] = datetime.utcnow()

        # 将 top_processes 列表转换为 JSON 字符串
        top_processes = metric_dict.pop("top_processes", None)
        if top_processes:
            metric_dict["top_processes"] = json.dumps(top_processes)

        # 将 disk_io_details 列表转换为 JSON 字符串
        disk_io_details = metric_dict.pop("disk_io_details", None)
        if disk_io_details:
            metric_dict["disk_io_details"] = json.dumps(disk_io_details)

        # Filter out keys that are not in the model to prevent TypeError
        valid_keys = {c.name for c in PerformanceMetric.__table__.columns}
        metric_dict = {k: v for k, v in metric_dict.items() if k in valid_keys}

        db_metric = PerformanceMetric(**metric_dict)
        db.add(db_metric)
        created_count += 1

    db.commit()
    return {"created": created_count}


@router.get("/metrics", response_model=PerformanceMetricListResponse)
def get_metrics(
    device_id: str = Query(..., description="设备ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_sync),
):
    """获取性能指标列表"""
    query = select(PerformanceMetric).where(PerformanceMetric.device_id == device_id)

    if start_time:
        query = query.where(PerformanceMetric.timestamp >= start_time)
    if end_time:
        query = query.where(PerformanceMetric.timestamp <= end_time)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Get paginated results
    query = (
        query.order_by(PerformanceMetric.timestamp.desc()).offset(offset).limit(limit)
    )
    results = db.execute(query).scalars().all()

    return {"total": total, "items": results}


@router.get("/metrics/latest", response_model=PerformanceMetricResponse)
def get_latest_metric(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备最新性能指标"""
    import json

    result = db.execute(
        select(PerformanceMetric)
        .where(PerformanceMetric.device_id == device_id)
        .order_by(PerformanceMetric.timestamp.desc())
        .limit(1)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="No metrics found for this device")

    # 转换为字典并解析 top_processes JSON 字符串
    metric_dict = {
        "id": metric.id,
        "device_id": metric.device_id,
        "timestamp": metric.timestamp,
        "cpu_percent": metric.cpu_percent,
        "cpu_temperature": metric.cpu_temperature,
        "cpu_power_watts": metric.cpu_power_watts,
        "cpu_frequency_mhz": metric.cpu_frequency_mhz,
        "gpu_percent": metric.gpu_percent,
        "gpu_temperature": metric.gpu_temperature,
        "gpu_power_watts": metric.gpu_power_watts,
        "gpu_frequency_mhz": metric.gpu_frequency_mhz,
        "gpu_memory_used_mb": metric.gpu_memory_used_mb,
        "gpu_memory_total_mb": metric.gpu_memory_total_mb,
        "memory_percent": metric.memory_percent,
        "memory_used_mb": metric.memory_used_mb,
        "memory_available_mb": metric.memory_available_mb,
        "disk_read_mbps": metric.disk_read_mbps,
        "disk_write_mbps": metric.disk_write_mbps,
        "disk_io_percent": metric.disk_io_percent,
        "network_sent_mbps": metric.network_sent_mbps,
        "network_recv_mbps": metric.network_recv_mbps,
        "process_count": metric.process_count,
        "top_processes": metric.top_processes,
        "raw_data": metric.raw_data,
        "created_at": metric.created_at,
    }

    # 解析 top_processes JSON 字符串
    if metric_dict["top_processes"]:
        if isinstance(metric_dict["top_processes"], str):
            try:
                metric_dict["top_processes"] = json.loads(metric_dict["top_processes"])
            except:
                metric_dict["top_processes"] = None

    # 解析 disk_io_details JSON 字符串
    if metric_dict.get("disk_io_details"):
        if isinstance(metric_dict["disk_io_details"], str):
            try:
                metric_dict["disk_io_details"] = json.loads(metric_dict["disk_io_details"])
            except:
                metric_dict["disk_io_details"] = None

    return metric_dict


@router.get("/metrics/realtime/{device_id}")
def get_realtime_metrics(
    device_id: str,
    seconds: int = Query(60, ge=10, le=3600),
    db: Session = Depends(get_db_sync),
):
    """获取实时性能指标 (最近N秒)"""
    import json

    since = datetime.utcnow() - timedelta(seconds=seconds)
    result = db.execute(
        select(PerformanceMetric)
        .where(PerformanceMetric.device_id == device_id)
        .where(PerformanceMetric.timestamp >= since)
        .order_by(PerformanceMetric.timestamp.asc())
    )
    metrics = result.scalars().all()

    # Calculate averages
    if not metrics:
        return {"device_id": device_id, "metrics": [], "averages": None}

    avg_cpu = sum(m.cpu_percent or 0 for m in metrics) / len(metrics)
    avg_gpu = sum(m.gpu_percent or 0 for m in metrics) / len(metrics)
    avg_memory = sum(m.memory_percent or 0 for m in metrics) / len(metrics)

    # Convert to dicts and parse JSON fields
    metrics_data = []
    for m in metrics:
        m_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
        
        # Parse disk_io_details
        if m_dict.get("disk_io_details"):
            if isinstance(m_dict["disk_io_details"], str):
                try:
                    m_dict["disk_io_details"] = json.loads(m_dict["disk_io_details"])
                except:
                    m_dict["disk_io_details"] = None
        
        # Parse top_processes
        if m_dict.get("top_processes"):
            if isinstance(m_dict["top_processes"], str):
                try:
                    m_dict["top_processes"] = json.loads(m_dict["top_processes"])
                except:
                    m_dict["top_processes"] = None
                    
        metrics_data.append(m_dict)

    return {
        "device_id": device_id,
        "metrics": metrics_data,
        "averages": {
            "cpu_percent": round(avg_cpu, 2),
            "gpu_percent": round(avg_gpu, 2),
            "memory_percent": round(avg_memory, 2),
        },
    }


# ==================== Software Benchmarks ====================


@router.post(
    "/benchmarks",
    response_model=SoftwareBenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_benchmark(
    benchmark: SoftwareBenchmarkCreate, db: Session = Depends(get_db_sync)
):
    """创建基准测试记录"""
    if not benchmark.timestamp:
        benchmark.timestamp = datetime.utcnow()
    db_benchmark = SoftwareBenchmark(**benchmark.model_dump())
    db.add(db_benchmark)
    db.commit()
    db.refresh(db_benchmark)
    return db_benchmark


@router.get("/benchmarks", response_model=SoftwareBenchmarkListResponse)
def get_benchmarks(
    device_id: Optional[str] = Query(None),
    software_code: Optional[str] = Query(None),
    benchmark_type: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_sync),
):
    """获取基准测试列表"""
    query = select(SoftwareBenchmark)

    if device_id:
        query = query.where(SoftwareBenchmark.device_id == device_id)
    if software_code:
        query = query.where(SoftwareBenchmark.software_code == software_code)
    if benchmark_type:
        query = query.where(SoftwareBenchmark.benchmark_type == benchmark_type)
    if start_time:
        query = query.where(SoftwareBenchmark.timestamp >= start_time)
    if end_time:
        query = query.where(SoftwareBenchmark.timestamp <= end_time)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Get paginated results
    query = (
        query.order_by(SoftwareBenchmark.timestamp.desc()).offset(offset).limit(limit)
    )
    results = db.execute(query).scalars().all()

    return {"total": total, "items": results}


@router.get("/benchmarks/{benchmark_id}", response_model=SoftwareBenchmarkResponse)
def get_benchmark(benchmark_id: str, db: Session = Depends(get_db_sync)):
    """获取基准测试详情"""
    result = db.execute(
        select(SoftwareBenchmark).where(SoftwareBenchmark.id == benchmark_id)
    )
    benchmark = result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark


@router.post("/benchmarks/start", response_model=SoftwareBenchmarkResponse)
def start_benchmark(request: BenchmarkStartRequest, db: Session = Depends(get_db_sync)):
    """开始基准测试"""
    # Verify device exists
    device_result = db.execute(select(Device).where(Device.id == request.device_id))
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Create benchmark record with pending status
    benchmark = SoftwareBenchmark(
        device_id=request.device_id,
        software_code=request.software_code,
        benchmark_type=request.benchmark_type,
        test_scene=request.test_scene,
        scene_file_path=request.scene_file_path,
        timestamp=datetime.utcnow(),
        status="running",
    )
    db.add(benchmark)
    db.commit()
    db.refresh(benchmark)

    return benchmark


@router.post("/benchmarks/{benchmark_id}/result")
def submit_benchmark_result(
    benchmark_id: str,
    result: BenchmarkResultRequest,
    db: Session = Depends(get_db_sync),
):
    """提交基准测试结果"""
    result_db = db.execute(
        select(SoftwareBenchmark).where(SoftwareBenchmark.id == benchmark_id)
    )
    benchmark = result_db.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")

    # Update benchmark with results
    benchmark.status = result.status
    benchmark.score = result.score
    benchmark.score_cpu = result.score_cpu
    benchmark.score_gpu = result.score_gpu
    benchmark.score_memory = result.score_memory
    benchmark.score_disk = result.score_disk
    benchmark.avg_fps = result.avg_fps
    benchmark.min_fps = result.min_fps
    benchmark.max_fps = result.max_fps
    benchmark.frame_count = result.frame_count
    benchmark.render_time_seconds = result.render_time_seconds
    benchmark.peak_cpu_percent = result.peak_cpu_percent
    benchmark.peak_gpu_percent = result.peak_gpu_percent
    benchmark.peak_memory_mb = result.peak_memory_mb
    benchmark.peak_gpu_memory_mb = result.peak_gpu_memory_mb
    benchmark.avg_cpu_percent = result.avg_cpu_percent
    benchmark.avg_gpu_percent = result.avg_gpu_percent
    benchmark.avg_memory_mb = result.avg_memory_mb
    benchmark.error_message = result.error_message
    benchmark.bottleneck_type = result.bottleneck_type
    benchmark.bottleneck_detail = result.bottleneck_detail
    benchmark.upgrade_suggestion = result.upgrade_suggestion

    db.commit()
    db.refresh(benchmark)

    return benchmark


# ==================== Control Commands ====================


@router.post(
    "/commands",
    response_model=ControlCommandResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_command(command: ControlCommandCreate, db: Session = Depends(get_db_sync)):
    """创建控制命令"""
    db_command = ControlCommand(**command.model_dump())
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    return db_command


@router.get("/commands", response_model=ControlCommandListResponse)
def get_commands(
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    command_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_sync),
):
    """获取控制命令列表"""
    query = select(ControlCommand)

    if device_id:
        query = query.where(ControlCommand.device_id == device_id)
    if status:
        query = query.where(ControlCommand.status == status)
    if command_type:
        query = query.where(ControlCommand.command_type == command_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Get paginated results
    query = query.order_by(ControlCommand.created_at.desc()).offset(offset).limit(limit)
    results = db.execute(query).scalars().all()

    return {"total": total, "items": results}


@router.get("/commands/pending", response_model=ControlCommandListResponse)
def get_pending_commands(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备的待执行命令"""
    result = db.execute(
        select(ControlCommand)
        .where(ControlCommand.device_id == device_id)
        .where(ControlCommand.status == "pending")
        .order_by(ControlCommand.priority.desc(), ControlCommand.created_at.asc())
    )
    commands = result.scalars().all()
    return {"total": len(commands), "items": commands}


@router.post("/commands/{command_id}/acknowledge")
def acknowledge_command(command_id: str, db: Session = Depends(get_db_sync)):
    """命令被设备确认接收"""
    result = db.execute(select(ControlCommand).where(ControlCommand.id == command_id))
    command = result.scalar_one_or_none()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")

    command.status = "executing"
    command.acknowledged_at = datetime.utcnow()
    db.commit()

    return {"status": "acknowledged"}


@router.post("/commands/{command_id}/complete")
def complete_command(
    command_id: str,
    result: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    """命令执行完成"""
    result_db = db.execute(
        select(ControlCommand).where(ControlCommand.id == command_id)
    )
    command = result_db.scalar_one_or_none()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")

    command.status = "completed" if not error_message else "failed"
    command.completed_at = datetime.utcnow()
    command.result = result
    command.error_message = error_message
    db.commit()

    return {"status": command.status}


# ==================== Performance Alerts ====================


@router.post(
    "/alerts",
    response_model=PerformanceAlertResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_alert(alert: PerformanceAlertCreate, db: Session = Depends(get_db_sync)):
    """创建性能告警"""
    db_alert = PerformanceAlert(**alert.model_dump())
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


@router.get("/alerts", response_model=PerformanceAlertListResponse)
def get_alerts(
    device_id: Optional[str] = Query(None),
    is_resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db_sync),
):
    """获取性能告警列表"""
    query = select(PerformanceAlert)

    if device_id:
        query = query.where(PerformanceAlert.device_id == device_id)
    if is_resolved is not None:
        query = query.where(PerformanceAlert.is_resolved == is_resolved)
    if severity:
        query = query.where(PerformanceAlert.severity == severity)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar()

    # Get paginated results
    query = (
        query.order_by(PerformanceAlert.created_at.desc()).offset(offset).limit(limit)
    )
    results = db.execute(query).scalars().all()

    return {"total": total, "items": results}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: str, resolved_by: str = Query(...), db: Session = Depends(get_db_sync)
):
    """解决告警"""
    result = db.execute(select(PerformanceAlert).where(PerformanceAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = resolved_by
    db.commit()

    return {"status": "resolved"}


# ==================== Device Status ====================


@router.get("/devices/{device_id}/status")
def get_device_status(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备实时状态"""
    # Get latest metric
    metric_result = db.execute(
        select(PerformanceMetric)
        .where(PerformanceMetric.device_id == device_id)
        .order_by(PerformanceMetric.timestamp.desc())
        .limit(1)
    )
    latest_metric = metric_result.scalar_one_or_none()

    # Get pending alerts
    alerts_result = db.execute(
        select(PerformanceAlert)
        .where(PerformanceAlert.device_id == device_id)
        .where(PerformanceAlert.is_resolved == False)
    )
    pending_alerts = alerts_result.scalars().all()

    # Get recent benchmarks
    benchmarks_result = db.execute(
        select(SoftwareBenchmark)
        .where(SoftwareBenchmark.device_id == device_id)
        .order_by(SoftwareBenchmark.timestamp.desc())
        .limit(5)
    )
    recent_benchmarks = benchmarks_result.scalars().all()

    return {
        "device_id": device_id,
        "latest_metric": latest_metric,
        "pending_alerts_count": len(pending_alerts),
        "recent_benchmarks": recent_benchmarks,
        "status": "online" if latest_metric else "offline",
    }

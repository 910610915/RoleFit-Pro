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
    """
    Create a new performance metric entry for a device.
    
    Records detailed hardware performance data including CPU, GPU, memory, disk, and network statistics
    for monitoring and analysis purposes.
    
    Args:
        metric (MetricDataCreate): The performance metric data containing:
            - device_id (str): Unique identifier of the device
            - cpu_percent (float, optional): CPU utilization percentage (0-100)
            - cpu_temperature (float, optional): CPU temperature in Celsius
            - cpu_power_watts (float, optional): CPU power consumption in watts
            - cpu_frequency_mhz (float, optional): CPU frequency in MHz
            - gpu_percent (float, optional): GPU utilization percentage (0-100)
            - gpu_temperature (float, optional): GPU temperature in Celsius
            - gpu_power_watts (float, optional): GPU power consumption in watts
            - gpu_frequency_mhz (float, optional): GPU frequency in MHz
            - gpu_memory_used_mb (float, optional): GPU memory used in MB
            - gpu_memory_total_mb (float, optional): GPU total memory in MB
            - memory_percent (float, optional): Memory utilization percentage (0-100)
            - memory_used_mb (float, optional): Memory used in MB
            - memory_available_mb (float, optional): Memory available in MB
            - disk_read_mbps (float, optional): Disk read speed in MB/s
            - disk_write_mbps (float, optional): Disk write speed in MB/s
            - disk_io_percent (float, optional): Disk I/O utilization percentage
            - network_sent_mbps (float, optional): Network send speed in Mbps
            - network_recv_mbps (float, optional): Network receive speed in Mbps
            - process_count (int, optional): Number of running processes
            - top_processes (list, optional): List of top resource-consuming processes
            - disk_io_details (list, optional): Detailed disk I/O information per partition
            - raw_data (dict, optional): Raw metric data for extensibility
            - timestamp (datetime, optional): Metric timestamp (defaults to current UTC time)
        
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        PerformanceMetricResponse: The created performance metric with all fields including:
            - id (int): Unique metric identifier
            - device_id (str): Device identifier
            - timestamp (datetime): Metric timestamp
            - All performance metric fields as stored in the database
    
    Raises:
        HTTPException: None (validation errors handled by FastAPI automatically)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/metrics" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "cpu_percent": 45.5,
            "memory_percent": 62.3,
            "gpu_percent": 78.2
          }'
        ```
    """
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
        disk_io_details=json.dumps(data.disk_io_details)
        if data.disk_io_details
        else None,
    )

    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)

    # 手动构建响应字典，因为 top_processes 和 disk_io_details 在数据库中是 JSON 字符串
    metric_dict = {
        c.name: getattr(db_metric, c.name) for c in db_metric.__table__.columns
    }

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
    """
    Create multiple performance metrics in a single batch operation.
    
    Efficiently records multiple metric data points for a device in one request,
    useful for bulk data imports or uploading cached metrics.
    
    Args:
        batch (MetricsBatchCreate): Batch containing:
            - device_id (str): Target device identifier for all metrics
            - metrics (list[MetricDataCreate]): List of metric data points to create
            
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        dict: Batch creation result containing:
            - created (int): Number of metrics successfully created
    
    Raises:
        HTTPException: None (validation errors handled by FastAPI automatically)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/metrics/batch" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "metrics": [
              {"cpu_percent": 45.5, "memory_percent": 62.3},
              {"cpu_percent": 48.1, "memory_percent": 63.1}
            ]
          }'
        ```
    """
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
    """
    Retrieve a paginated list of performance metrics for a specific device.

    Queries historical performance data with optional time range filtering,
    sorted by timestamp in descending order (newest first).

    Args:
        device_id (str): Unique identifier of the device to fetch metrics for
        start_time (datetime, optional): Filter metrics recorded after this time (inclusive)
        end_time (datetime, optional): Filter metrics recorded before this time (inclusive)
        limit (int): Maximum number of metrics to return (default: 100, range: 1-1000)
        offset (int): Number of metrics to skip for pagination (default: 0)
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        PerformanceMetricListResponse: Paginated response containing:
            - total (int): Total number of metrics matching the query
            - items (list[PerformanceMetric]): List of performance metrics

    Raises:
        HTTPException: None (returns empty list if no metrics found)

    Example:
        ```bash
        # Get latest 50 metrics for a device
        curl "http://localhost:8000/api/performance/metrics?device_id=dev-001&limit=50"

        # Get metrics within a time range
        curl "http://localhost:8000/api/performance/metrics?device_id=dev-001&start_time=2024-01-01T00:00:00&end_time=2024-01-02T00:00:00"
        ```
    """
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
    """
    Retrieve the most recent performance metric for a specific device.

    Returns the latest recorded metric based on timestamp, useful for
    displaying current device status in dashboards or实时 views.

    Args:
        device_id (str): Unique identifier of the device to fetch the latest metric for
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        PerformanceMetricResponse: The most recent performance metric including:
            - id (int): Unique metric identifier
            - device_id (str): Device identifier
            - timestamp (datetime): Metric timestamp
            - cpu_percent (float): CPU utilization percentage
            - gpu_percent (float): GPU utilization percentage
            - memory_percent (float): Memory utilization percentage
            - All other performance metric fields

    Raises:
        HTTPException: 404 Not Found if no metrics exist for the specified device

    Example:
        ```bash
        curl "http://localhost:8000/api/performance/metrics/latest?device_id=dev-001"
        ```
    """
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
                metric_dict["disk_io_details"] = json.loads(
                    metric_dict["disk_io_details"]
                )
            except:
                metric_dict["disk_io_details"] = None

    return metric_dict


@router.get("/metrics/realtime/{device_id}")
def get_realtime_metrics(
    device_id: str,
    seconds: int = Query(60, ge=10, le=3600),
    start_time: Optional[datetime] = Query(None, description="开始时间 (ISO格式)"),
    end_time: Optional[datetime] = Query(None, description="结束时间 (ISO格式)"),
    db: Session = Depends(get_db_sync),
):
    """
    Retrieve realtime or historical performance metrics for a device with calculated averages.

    Returns metrics within a specified time window, either as recent N seconds or
    a custom time range. Includes calculated average values for key metrics.

    Args:
        device_id (str): Unique identifier of the device
        seconds (int): Time window in seconds for recent metrics (default: 60, range: 10-3600)
            Ignored if start_time and end_time are both provided
        start_time (datetime, optional): Start of custom time range (ISO format)
        end_time (datetime, optional): End of custom time range (ISO format)
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        dict: Realtime metrics data containing:
            - device_id (str): Device identifier
            - metrics (list[PerformanceMetric]): List of metrics in time order
            - averages (dict): Calculated average values:
                - cpu_percent (float): Average CPU utilization
                - gpu_percent (float): Average GPU utilization
                - memory_percent (float): Average memory utilization

    Raises:
        HTTPException: None (returns empty metrics list if no data found)

    Example:
        ```bash
        # Get last 5 minutes of metrics
        curl "http://localhost:8000/api/performance/metrics/realtime/dev-001?seconds=300"

        # Get metrics for specific time range
        curl "http://localhost:8000/api/performance/metrics/realtime/dev-001?start_time=2024-01-15T10:00:00&end_time=2024-01-15T11:00:00"
        ```
    """
    import json

    # 如果提供了日期范围参数，优先使用日期范围
    if start_time and end_time:
        # 日期范围查询
        result = db.execute(
            select(PerformanceMetric)
            .where(PerformanceMetric.device_id == device_id)
            .where(PerformanceMetric.timestamp >= start_time)
            .where(PerformanceMetric.timestamp <= end_time)
            .order_by(PerformanceMetric.timestamp.asc())
        )
    else:
        # 使用默认的最近N秒
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
    """
    Create a new software benchmark record.
    
    Records benchmark test metadata before execution, including device info,
    software details, and test configuration.
    
    Args:
        benchmark (SoftwareBenchmarkCreate): Benchmark configuration containing:
            - device_id (str): Target device identifier
            - software_code (str): Software identifier code
            - benchmark_type (str): Type of benchmark (e.g., "blender", "maya", "unreal")
            - test_scene (str, optional): Test scene name or identifier
            - scene_file_path (str, optional): Path to scene file used
            - timestamp (datetime, optional): Benchmark timestamp (defaults to current UTC)
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        SoftwareBenchmarkResponse: The created benchmark record including:
            - id (str): Unique benchmark identifier
            - device_id (str): Device identifier
            - software_code (str): Software code
            - benchmark_type (str): Benchmark type
            - status (str): Initial status ("pending")
            - All other benchmark fields
    
    Raises:
        HTTPException: None (validation errors handled by FastAPI automatically)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/benchmarks" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "software_code": "blender-3.6",
            "benchmark_type": "render",
            "test_scene": "classroom"
          }'
        ```
    """
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
    """
    Retrieve a paginated list of benchmark records with optional filtering.

    Queries historical benchmark data with support for filtering by device,
    software, benchmark type, and time range.

    Args:
        device_id (str, optional): Filter by device identifier
        software_code (str, optional): Filter by software code
        benchmark_type (str, optional): Filter by benchmark type (e.g., "render", "compile")
        start_time (datetime, optional): Filter benchmarks after this time
        end_time (datetime, optional): Filter benchmarks before this time
        limit (int): Maximum number of results (default: 50, range: 1-500)
        offset (int): Number of results to skip for pagination (default: 0)
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        SoftwareBenchmarkListResponse: Paginated benchmark results containing:
            - total (int): Total number of benchmarks matching filters
            - items (list[SoftwareBenchmark]): List of benchmark records

    Raises:
        HTTPException: None (returns empty list if no benchmarks found)

    Example:
        ```bash
        # Get all benchmarks for a device
        curl "http://localhost:8000/api/performance/benchmarks?device_id=dev-001"

        # Get Blender renders from the last week
        curl "http://localhost:8000/api/performance/benchmarks?benchmark_type=render&start_time=2024-01-08T00:00:00"
        ```
    """
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
    """
    Retrieve a specific benchmark record by its unique identifier.

    Returns complete benchmark details including scores, performance metrics,
    and any error information if the benchmark failed.

    Args:
        benchmark_id (str): Unique identifier of the benchmark to retrieve
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        SoftwareBenchmarkResponse: Complete benchmark record containing:
            - id (str): Benchmark identifier
            - device_id (str): Device identifier
            - software_code (str): Software code
            - benchmark_type (str): Benchmark type
            - status (str): Benchmark status (pending/running/completed/failed)
            - score (float, optional): Overall benchmark score
            - score_cpu, score_gpu, score_memory, score_disk (float, optional): Component scores
            - avg_fps, min_fps, max_fps (float, optional): Frame rate statistics
            - peak_cpu_percent, peak_gpu_percent (float, optional): Peak utilization
            - bottleneck_type (str, optional): Identified bottleneck
            - upgrade_suggestion (str, optional): Upgrade recommendations

    Raises:
        HTTPException: 404 Not Found if no benchmark exists with the given ID

    Example:
        ```bash
        curl "http://localhost:8000/api/performance/benchmarks/bmark-12345"
        ```
    """
    result = db.execute(
        select(SoftwareBenchmark).where(SoftwareBenchmark.id == benchmark_id)
    )
    benchmark = result.scalar_one_or_none()
    if not benchmark:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return benchmark


@router.post("/benchmarks/start", response_model=SoftwareBenchmarkResponse)
def start_benchmark(request: BenchmarkStartRequest, db: Session = Depends(get_db_sync)):
    """
    Initiate a new benchmark test on a specified device.
    
    Creates a benchmark record with "running" status after verifying the device exists.
    The actual benchmark execution is performed by the device agent.
    
    Args:
        request (BenchmarkStartRequest): Benchmark start request containing:
            - device_id (str): Target device identifier
            - software_code (str): Software to benchmark
            - benchmark_type (str): Type of benchmark test
            - test_scene (str, optional): Test scene name
            - scene_file_path (str, optional): Path to scene file
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        SoftwareBenchmarkResponse: The created benchmark record with status="running"
    
    Raises:
        HTTPException: 404 Not Found if the specified device does not exist
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/benchmarks/start" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "software_code": "blender-3.6",
            "benchmark_type": "render",
            "test_scene": "classroom"
          }'
        ```
    """
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
    """
    Submit the results of a completed benchmark test.
    
    Updates the benchmark record with scores, performance metrics, and final status.
    Called by the device agent after benchmark execution completes.
    
    Args:
        benchmark_id (str): Unique identifier of the benchmark to update
        result (BenchmarkResultRequest): Benchmark results containing:
            - status (str): Final status ("completed" or "failed")
            - score (float, optional): Overall benchmark score
            - score_cpu (float, optional): CPU benchmark score
            - score_gpu (float, optional): GPU benchmark score
            - score_memory (float, optional): Memory benchmark score
            - score_disk (float, optional): Disk benchmark score
            - avg_fps (float, optional): Average frames per second
            - min_fps (float, optional): Minimum frames per second
            - max_fps (float, optional): Maximum frames per second
            - frame_count (int, optional): Total frames rendered
            - render_time_seconds (float, optional): Total render time
            - peak_cpu_percent (float, optional): Peak CPU utilization
            - peak_gpu_percent (float, optional): Peak GPU utilization
            - peak_memory_mb (float, optional): Peak memory usage
            - peak_gpu_memory_mb (float, optional): Peak GPU memory usage
            - avg_cpu_percent (float, optional): Average CPU utilization
            - avg_gpu_percent (float, optional): Average GPU utilization
            - avg_memory_mb (float, optional): Average memory usage
            - error_message (str, optional): Error details if failed
            - bottleneck_type (str, optional): Identified bottleneck (cpu/gpu/memory/disk)
            - bottleneck_detail (str, optional): Detailed bottleneck analysis
            - upgrade_suggestion (str, optional): Hardware upgrade recommendations
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        SoftwareBenchmarkResponse: The updated benchmark record
    
    Raises:
        HTTPException: 404 Not Found if no benchmark exists with the given ID
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/benchmarks/bmark-12345/result" \\
          -H "Content-Type: application/json" \\
          -d '{
            "status": "completed",
            "score": 12500,
            "score_gpu": 15200,
            "avg_fps": 45.2,
            "peak_gpu_percent": 98.5
          }'
        ```
    """
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
    """
    Create a new control command for a device.
    
    Queues a command for a device to execute, such as shutdown, restart, or
    software installation. Commands are pulled by the device agent.
    
    Args:
        command (ControlCommandCreate): Command configuration containing:
            - device_id (str): Target device identifier
            - command_type (str): Type of command (e.g., "shutdown", "restart", "install")
            - priority (int, optional): Command priority (higher = more urgent, default: 0)
            - parameters (dict, optional): Command-specific parameters
            - scheduled_at (datetime, optional): Scheduled execution time
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        ControlCommandResponse: The created command including:
            - id (str): Unique command identifier
            - device_id (str): Target device
            - command_type (str): Command type
            - status (str): Initial status ("pending")
            - priority (int): Command priority
            - created_at (datetime): Creation timestamp
    
    Raises:
        HTTPException: None (validation errors handled by FastAPI automatically)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/commands" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "command_type": "shutdown",
            "priority": 10
          }'
        ```
    """
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
    """
    Retrieve a paginated list of control commands with optional filtering.

    Queries command history with support for filtering by device, status, and type.

    Args:
        device_id (str, optional): Filter by device identifier
        status (str, optional): Filter by command status ("pending", "executing", "completed", "failed")
        command_type (str, optional): Filter by command type (e.g., "shutdown", "restart")
        limit (int): Maximum number of results (default: 50, range: 1-500)
        offset (int): Number of results to skip for pagination (default: 0)
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        ControlCommandListResponse: Paginated command results containing:
            - total (int): Total number of commands matching filters
            - items (list[ControlCommand]): List of command records

    Raises:
        HTTPException: None (returns empty list if no commands found)

    Example:
        ```bash
        # Get all pending commands for a device
        curl "http://localhost:8000/api/performance/commands?device_id=dev-001&status=pending"

        # Get all shutdown commands
        curl "http://localhost:8000/api/performance/commands?command_type=shutdown"
        ```
    """
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
    """
    Retrieve all pending (unexecuted) commands for a specific device.

    Returns commands ordered by priority (highest first) then by creation time (oldest first),
    suitable for a device to poll and retrieve its next commands to execute.

    Args:
        device_id (str): Unique identifier of the device to fetch pending commands for
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        ControlCommandListResponse: List of pending commands containing:
            - total (int): Number of pending commands
            - items (list[ControlCommand]): List of pending command records ordered by priority desc, created_at asc

    Raises:
        HTTPException: None (returns empty list if no pending commands)

    Example:
        ```bash
        curl "http://localhost:8000/api/performance/commands/pending?device_id=dev-001"
        ```
    """
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
    """
    Acknowledge receipt of a command by the target device.

    Called by the device agent when it receives and starts processing a command.
    Changes the command status from "pending" to "executing".

    Args:
        command_id (str): Unique identifier of the command to acknowledge
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        dict: Acknowledgment confirmation containing:
            - status (str): Confirmation status ("acknowledged")

    Raises:
        HTTPException: 404 Not Found if no command exists with the given ID

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/commands/cmd-12345/acknowledge"
        ```
    """
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
    """
    Mark a command as completed (success or failure) by the device.

    Called by the device agent when command execution finishes. If error_message
    is provided, the command status is set to "failed"; otherwise it is "completed".

    Args:
        command_id (str): Unique identifier of the command to complete
        result (str, optional): Execution result or output from the command
        error_message (str, optional): Error details if command failed
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        dict: Completion confirmation containing:
            - status (str): Final status ("completed" or "failed")

    Raises:
        HTTPException: 404 Not Found if no command exists with the given ID

    Example:
        ```bash
        # Successful completion
        curl -X POST "http://localhost:8000/api/performance/commands/cmd-12345/complete?result=Shutdown initiated successfully"

        # Failed completion
        curl -X POST "http://localhost:8000/api/performance/commands/cmd-12345/complete?error_message=Insufficient permissions"
        ```
    """
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
    """
    Create a new performance alert for a device.
    
    Records an alert when a performance threshold is exceeded, such as high CPU
    temperature, low disk space, or high memory usage.
    
    Args:
        alert (PerformanceAlertCreate): Alert configuration containing:
            - device_id (str): Target device identifier
            - alert_type (str): Type of alert (e.g., "high_cpu_temp", "low_disk_space", "high_memory")
            - severity (str): Alert severity ("info", "warning", "critical")
            - message (str): Human-readable alert message
            - metric_value (float, optional): The metric value that triggered the alert
            - threshold (float, optional): The threshold that was exceeded
            - metric_name (str, optional): Name of the metric that triggered the alert
        db (Session): SQLAlchemy database session (injected via dependency)
    
    Returns:
        PerformanceAlertResponse: The created alert including:
            - id (str): Unique alert identifier
            - device_id (str): Device identifier
            - alert_type (str): Alert type
            - severity (str): Alert severity
            - message (str): Alert message
            - is_resolved (bool): Resolution status (false)
            - created_at (datetime): Alert creation timestamp
    
    Raises:
        HTTPException: None (validation errors handled by FastAPI automatically)
    
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/alerts" \\
          -H "Content-Type: application/json" \\
          -d '{
            "device_id": "dev-001",
            "alert_type": "high_cpu_temp",
            "severity": "warning",
            "message": "CPU temperature exceeded 85°C",
            "metric_value": 87.5,
            "threshold": 85.0,
            "metric_name": "cpu_temperature"
          }'
        ```
    """
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
    """
    Retrieve a paginated list of performance alerts with optional filtering.

    Queries alert history with support for filtering by device, resolution status, and severity.

    Args:
        device_id (str, optional): Filter by device identifier
        is_resolved (bool, optional): Filter by resolution status (true = resolved, false = unresolved)
        severity (str, optional): Filter by severity level ("info", "warning", "critical")
        limit (int): Maximum number of results (default: 50, range: 1-500)
        offset (int): Number of results to skip for pagination (default: 0)
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        PerformanceAlertListResponse: Paginated alert results containing:
            - total (int): Total number of alerts matching filters
            - items (list[PerformanceAlert]): List of alert records

    Raises:
        HTTPException: None (returns empty list if no alerts found)

    Example:
        ```bash
        # Get all unresolved alerts for a device
        curl "http://localhost:8000/api/performance/alerts?device_id=dev-001&is_resolved=false"

        # Get all critical alerts
        curl "http://localhost:8000/api/performance/alerts?severity=critical"
        ```
    """
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
    """
    Mark a performance alert as resolved.

    Records the resolution of an alert including who resolved it and when.

    Args:
        alert_id (str): Unique identifier of the alert to resolve
        resolved_by (str): Identifier of the user or system that resolved the alert
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        dict: Resolution confirmation containing:
            - status (str): Resolution status ("resolved")

    Raises:
        HTTPException: 404 Not Found if no alert exists with the given ID

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/performance/alerts/alert-12345/resolve?resolved_by=admin"
        ```
    """
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
    """
    Retrieve the current real-time status summary of a device.

    Provides an overview including the latest metric, pending alerts count,
    recent benchmarks, and online/offline status based on metric availability.

    Args:
        device_id (str): Unique identifier of the device to get status for
        db (Session): SQLAlchemy database session (injected via dependency)

    Returns:
        dict: Device status summary containing:
            - device_id (str): Device identifier
            - latest_metric (PerformanceMetric or None): Most recent performance metric
            - pending_alerts_count (int): Number of unresolved alerts
            - recent_benchmarks (list[SoftwareBenchmark]): Last 5 benchmark records
            - status (str): Device status ("online" if latest_metric exists, "offline" otherwise)

    Raises:
        HTTPException: None (returns offline status with null metric if no data)

    Example:
        ```bash
        curl "http://localhost:8000/api/performance/devices/dev-001/status"
        ```
    """
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

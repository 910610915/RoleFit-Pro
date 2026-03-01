from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# PerformanceMetric Schemas
class PerformanceMetricBase(BaseModel):
    device_id: str
    timestamp: datetime


class PerformanceMetricCreate(PerformanceMetricBase):
    cpu_percent: Optional[float] = None
    cpu_temperature: Optional[float] = None
    cpu_power_watts: Optional[float] = None
    cpu_frequency_mhz: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_temperature: Optional[float] = None
    gpu_power_watts: Optional[float] = None
    gpu_frequency_mhz: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_available_mb: Optional[float] = None
    disk_read_mbps: Optional[float] = None
    disk_write_mbps: Optional[float] = None
    disk_io_percent: Optional[float] = None
    network_sent_mbps: Optional[float] = None
    network_recv_mbps: Optional[float] = None
    process_count: Optional[int] = None
    top_processes: Optional[str] = None
    raw_data: Optional[str] = None


class PerformanceMetricResponse(PerformanceMetricBase):
    id: str
    cpu_percent: Optional[float] = None
    cpu_temperature: Optional[float] = None
    cpu_power_watts: Optional[float] = None
    cpu_frequency_mhz: Optional[float] = None
    gpu_percent: Optional[float] = None
    gpu_temperature: Optional[float] = None
    gpu_power_watts: Optional[float] = None
    gpu_frequency_mhz: Optional[float] = None
    gpu_memory_used_mb: Optional[float] = None
    gpu_memory_total_mb: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used_mb: Optional[float] = None
    memory_available_mb: Optional[float] = None
    disk_read_mbps: Optional[float] = None
    disk_write_mbps: Optional[float] = None
    disk_io_percent: Optional[float] = None
    network_sent_mbps: Optional[float] = None
    network_recv_mbps: Optional[float] = None
    process_count: Optional[int] = None
    top_processes: Optional[str] = None
    raw_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceMetricListResponse(BaseModel):
    total: int
    items: List[PerformanceMetricResponse]


# SoftwareBenchmark Schemas
class SoftwareBenchmarkBase(BaseModel):
    device_id: str
    software_code: str
    benchmark_type: str


class SoftwareBenchmarkCreate(SoftwareBenchmarkBase):
    test_scene: Optional[str] = None
    scene_file_path: Optional[str] = None
    timestamp: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    score: Optional[float] = None
    score_cpu: Optional[float] = None
    score_gpu: Optional[float] = None
    score_memory: Optional[float] = None
    score_disk: Optional[float] = None
    avg_fps: Optional[float] = None
    min_fps: Optional[float] = None
    max_fps: Optional[float] = None
    frame_count: Optional[int] = None
    render_time_seconds: Optional[float] = None
    peak_cpu_percent: Optional[float] = None
    peak_gpu_percent: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    peak_gpu_memory_mb: Optional[float] = None
    avg_cpu_percent: Optional[float] = None
    avg_gpu_percent: Optional[float] = None
    avg_memory_mb: Optional[float] = None
    status: Optional[str] = "success"
    error_message: Optional[str] = None
    log_file_path: Optional[str] = None
    bottleneck_type: Optional[str] = None
    bottleneck_detail: Optional[str] = None
    upgrade_suggestion: Optional[str] = None


class SoftwareBenchmarkResponse(SoftwareBenchmarkBase):
    id: str
    test_scene: Optional[str] = None
    scene_file_path: Optional[str] = None
    timestamp: datetime
    duration_seconds: Optional[int] = None
    score: Optional[float] = None
    score_cpu: Optional[float] = None
    score_gpu: Optional[float] = None
    score_memory: Optional[float] = None
    score_disk: Optional[float] = None
    avg_fps: Optional[float] = None
    min_fps: Optional[float] = None
    max_fps: Optional[float] = None
    frame_count: Optional[int] = None
    render_time_seconds: Optional[float] = None
    peak_cpu_percent: Optional[float] = None
    peak_gpu_percent: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    peak_gpu_memory_mb: Optional[float] = None
    avg_cpu_percent: Optional[float] = None
    avg_gpu_percent: Optional[float] = None
    avg_memory_mb: Optional[float] = None
    status: Optional[str] = None
    error_message: Optional[str] = None
    log_file_path: Optional[str] = None
    bottleneck_type: Optional[str] = None
    bottleneck_detail: Optional[str] = None
    upgrade_suggestion: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SoftwareBenchmarkListResponse(BaseModel):
    total: int
    items: List[SoftwareBenchmarkResponse]


# ControlCommand Schemas
class ControlCommandBase(BaseModel):
    device_id: str
    command_type: str


class ControlCommandCreate(ControlCommandBase):
    target_software: Optional[str] = None
    command_params: Optional[str] = None
    priority: int = 5
    source: Optional[str] = "manual"
    triggered_by: Optional[str] = None


class ControlCommandUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


class ControlCommandResponse(ControlCommandBase):
    id: str
    target_software: Optional[str] = None
    command_params: Optional[str] = None
    status: str
    priority: int
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None
    triggered_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ControlCommandListResponse(BaseModel):
    total: int
    items: List[ControlCommandResponse]


# PerformanceAlert Schemas
class PerformanceAlertBase(BaseModel):
    device_id: str
    alert_type: str
    severity: str
    metric_name: str
    title: str
    message: str


class PerformanceAlertCreate(PerformanceAlertBase):
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    suggestion: Optional[str] = None
    benchmark_id: Optional[str] = None


class PerformanceAlertUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    resolved_by: Optional[str] = None


class PerformanceAlertResponse(PerformanceAlertBase):
    id: str
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    suggestion: Optional[str] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    benchmark_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceAlertListResponse(BaseModel):
    total: int
    items: List[PerformanceAlertResponse]


# AIAnalysisReport Schemas
class AIAnalysisReportBase(BaseModel):
    device_id: str
    analysis_type: str
    title: str


class AIAnalysisReportCreate(AIAnalysisReportBase):
    summary: Optional[str] = None
    details: Optional[str] = None
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None
    related_metrics: Optional[str] = None
    related_benchmarks: Optional[str] = None


class AIAnalysisReportResponse(AIAnalysisReportBase):
    id: str
    summary: Optional[str] = None
    details: Optional[str] = None
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None
    status: Optional[str] = None
    related_metrics: Optional[str] = None
    related_benchmarks: Optional[str] = None
    model_used: Optional[str] = None
    analysis_duration_ms: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIAnalysisReportListResponse(BaseModel):
    total: int
    items: List[AIAnalysisReportResponse]


# API Request/Response Schemas for batch operations
class MetricsBatchCreate(BaseModel):
    """批量创建性能指标"""

    device_id: str
    metrics: List[PerformanceMetricCreate]


class BenchmarkStartRequest(BaseModel):
    """开始基准测试请求"""

    device_id: str
    software_code: str
    benchmark_type: str
    test_scene: Optional[str] = None
    scene_file_path: Optional[str] = None
    command_params: Optional[str] = None


class BenchmarkResultRequest(BaseModel):
    """基准测试结果上报"""

    benchmark_id: str
    status: str
    score: Optional[float] = None
    score_cpu: Optional[float] = None
    score_gpu: Optional[float] = None
    score_memory: Optional[float] = None
    score_disk: Optional[float] = None
    avg_fps: Optional[float] = None
    min_fps: Optional[float] = None
    max_fps: Optional[float] = None
    frame_count: Optional[int] = None
    render_time_seconds: Optional[float] = None
    peak_cpu_percent: Optional[float] = None
    peak_gpu_percent: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    peak_gpu_memory_mb: Optional[float] = None
    avg_cpu_percent: Optional[float] = None
    avg_gpu_percent: Optional[float] = None
    avg_memory_mb: Optional[float] = None
    error_message: Optional[str] = None
    bottleneck_type: Optional[str] = None
    bottleneck_detail: Optional[str] = None
    upgrade_suggestion: Optional[str] = None


class AIAnalysisRequest(BaseModel):
    """AI分析请求"""

    device_id: Optional[str] = None
    query: Optional[str] = None
    analysis_type: str = (
        "general"  # performance_trend, bottleneck, upgrade_recommendation, general
    )
    title: Optional[str] = None
    metrics_period_hours: int = 24  # 分析最近多少小时的数据
    include_benchmarks: bool = True


class AIAnalysisResponse(BaseModel):
    """AI分析响应"""

    report_id: str
    status: str
    summary: Optional[str] = None
    conclusions: Optional[str] = None
    recommendations: Optional[str] = None
    details: Optional[dict] = None

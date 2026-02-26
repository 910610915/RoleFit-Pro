from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


# Result Schemas
class TestResultBase(BaseModel):
    task_id: Optional[str] = None
    device_id: str
    test_type: Optional[str] = None
    test_status: Optional[str] = None  # passed, failed, warning, partial
    start_time: datetime
    end_time: datetime
    duration_seconds: int


class TestResultCreate(TestResultBase):
    pass


class TestResultUpdate(BaseModel):
    test_status: Optional[str] = None
    overall_score: Optional[float] = None
    is_standard_met: Optional[bool] = None


class TestResultResponse(TestResultBase):
    id: str
    overall_score: Optional[float] = None
    cpu_score: Optional[float] = None
    gpu_score: Optional[float] = None
    memory_score: Optional[float] = None
    disk_score: Optional[float] = None
    is_standard_met: Optional[bool] = None
    standard_id: Optional[str] = None
    fail_reasons: Optional[Dict[str, Any]] = None
    performance_summary: Optional[Dict[str, Any]] = None
    bottleneck_type: Optional[str] = None
    bottleneck_detail: Optional[Dict[str, Any]] = None
    upgrade_suggestion: Optional[Dict[str, Any]] = None
    result_file_path: Optional[str] = None
    log_file_path: Optional[str] = None
    created_at: datetime

    @field_validator('fail_reasons', 'performance_summary', 'bottleneck_detail', 'upgrade_suggestion', mode='before')
    @classmethod
    def parse_json_string(cls, v):
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except:
                return None
        return v

    class Config:
        from_attributes = True


class TestResultListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TestResultResponse]


class ResultStatistics(BaseModel):
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    average_score: float
    average_cpu_score: float
    average_gpu_score: float
    average_memory_score: float
    average_disk_score: float
    standard_compliance_rate: float
    top_bottlenecks: Dict[str, int]


class DevicePerformanceSummary(BaseModel):
    device_id: str
    device_name: str
    total_tests: int
    latest_score: Optional[float]
    average_score: Optional[float]
    trend: Optional[str]  # improving, declining, stable
    last_test_time: Optional[datetime]

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Task Schemas
class TestTaskBase(BaseModel):
    task_name: str
    task_type: str  # benchmark, simulation, full, custom
    target_device_ids: Optional[List[str]] = []
    target_departments: Optional[List[str]] = []
    target_positions: Optional[List[str]] = []
    test_script_id: Optional[str] = None
    test_duration_seconds: Optional[int] = None
    sample_interval_ms: int = 1000
    schedule_type: Optional[str] = None  # immediate, scheduled, recurring
    scheduled_at: Optional[datetime] = None
    cron_expression: Optional[str] = None


class TestTaskCreate(TestTaskBase):
    pass


class TestTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_status: Optional[str] = None
    target_device_ids: Optional[List[str]] = None
    test_duration_seconds: Optional[int] = None


class TestTaskResponse(TestTaskBase):
    id: str
    task_status: str
    assigned_agent_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestTaskListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TestTaskResponse]


class TaskExecuteRequest(BaseModel):
    device_ids: List[str]


class TaskCancelRequest(BaseModel):
    reason: Optional[str] = None

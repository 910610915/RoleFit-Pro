from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExecutionBase(BaseModel):
    task_id: Optional[str] = None
    script_id: Optional[str] = None
    device_id: Optional[str] = None


class ExecutionCreate(ExecutionBase):
    pass


class ExecutionUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None


class ExecutionResponse(ExecutionBase):
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    exit_code: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ExecutionResponse]

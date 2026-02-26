from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PositionBase(BaseModel):
    position_name: str
    position_code: str
    department: Optional[str] = None
    description: Optional[str] = None


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    position_name: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class PositionResponse(PositionBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PositionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PositionResponse]

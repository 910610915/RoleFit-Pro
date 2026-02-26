from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json


class ScriptBase(BaseModel):
    script_name: str
    script_code: str
    position_ids: Optional[List[str]] = []  # 支持多个岗位
    software_id: Optional[str] = None
    script_type: Optional[str] = None  # START/OPERATION/RENDER/STRESS/BENCHMARK
    script_content: str  # JSON string
    expected_duration: Optional[int] = 300


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    script_name: Optional[str] = None
    position_ids: Optional[List[str]] = None
    software_id: Optional[str] = None
    script_type: Optional[str] = None
    script_content: Optional[str] = None
    expected_duration: Optional[int] = None
    is_active: Optional[bool] = None


class ScriptResponse(ScriptBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        # 解析position_ids JSON字段
        if hasattr(obj, 'position_ids'):
            if obj.position_ids:
                try:
                    obj.position_ids = json.loads(obj.position_ids) if isinstance(obj.position_ids, str) else obj.position_ids
                except:
                    obj.position_ids = []
            else:
                obj.position_ids = []
        return super().model_validate(obj, **kwargs)


class ScriptListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ScriptResponse]

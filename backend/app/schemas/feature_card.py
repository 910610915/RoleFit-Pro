from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FeatureCardBase(BaseModel):
    card_key: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    route: Optional[str] = None
    is_visible: bool = True
    sort_order: int = 0


class FeatureCardCreate(FeatureCardBase):
    pass


class FeatureCardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    route: Optional[str] = None
    is_visible: Optional[bool] = None
    sort_order: Optional[int] = None


class FeatureCardResponse(FeatureCardBase):
    id: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureCardListResponse(BaseModel):
    items: list[FeatureCardResponse]
    total: int

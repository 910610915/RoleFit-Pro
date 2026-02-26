from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional
import uuid

from app.core.database import get_db_sync
from app.models.sqlite import FeatureCard
from app.schemas.feature_card import (
    FeatureCardCreate, FeatureCardUpdate, 
    FeatureCardResponse, FeatureCardListResponse
)

router = APIRouter(prefix="/feature-cards", tags=["Feature Cards"])

# Default feature cards
DEFAULT_CARDS = [
    {"card_key": "devices", "title": "设备管理", "description": "集中查看所有开发设备状态", "icon": "desktop", "route": "/devices", "sort_order": 1},
    {"card_key": "positions", "title": "岗位管理", "description": "预设岗位配置和自定义需求", "icon": "people", "route": "/positions", "sort_order": 2},
    {"card_key": "software", "title": "软件管理", "description": "测试软件库和版本管理", "icon": "apps", "route": "/software", "sort_order": 3},
    {"card_key": "scripts", "title": "脚本管理", "description": "岗位测试脚本库", "icon": "code", "route": "/scripts", "sort_order": 4},
    {"card_key": "tasks", "title": "任务管理", "description": "创建和调度性能测试任务", "icon": "list", "route": "/tasks", "sort_order": 5},
    {"card_key": "executions", "title": "执行记录", "description": "测试执行历史和详情", "icon": "play", "route": "/executions", "sort_order": 6},
    {"card_key": "compare", "title": "设备对比", "description": "多设备性能对比分析", "icon": "git-compare", "route": "/compare", "sort_order": 7},
    {"card_key": "results", "title": "数据分析", "description": "性能趋势和达标判定", "icon": "stats", "route": "/results", "sort_order": 8},
]


@router.get("", response_model=FeatureCardListResponse)
def list_feature_cards(db: Session = Depends(get_db_sync)):
    """获取所有功能卡片配置"""
    # Check if there are any cards in DB
    result = db.execute(select(FeatureCard))
    cards = result.scalars().all()
    
    # If no cards in DB, initialize with defaults
    if not cards:
        for card_data in DEFAULT_CARDS:
            card = FeatureCard(
                id=str(uuid.uuid4()),
                card_key=card_data["card_key"],
                title=card_data["title"],
                description=card_data.get("description"),
                icon=card_data.get("icon"),
                route=card_data.get("route"),
                sort_order=card_data.get("sort_order", 0),
                is_visible=True,
                is_custom=False
            )
            db.add(card)
        db.commit()
        
        # Fetch again
        result = db.execute(select(FeatureCard).order_by(FeatureCard.sort_order))
        cards = result.scalars().all()
    
    return FeatureCardListResponse(
        items=[FeatureCardResponse.model_validate(card) for card in cards],
        total=len(cards)
    )


@router.get("/{card_id}", response_model=FeatureCardResponse)
def get_feature_card(card_id: str, db: Session = Depends(get_db_sync)):
    """获取单个功能卡片配置"""
    result = db.execute(select(FeatureCard).where(FeatureCard.id == card_id))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return card


@router.post("", response_model=FeatureCardResponse, status_code=status.HTTP_201_CREATED)
def create_feature_card(data: FeatureCardCreate, db: Session = Depends(get_db_sync)):
    """创建自定义功能卡片"""
    # Check if card_key already exists
    result = db.execute(select(FeatureCard).where(FeatureCard.card_key == data.card_key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Card key already exists")
    
    card = FeatureCard(
        id=str(uuid.uuid4()),
        **data.model_dump(),
        is_custom=True
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    
    return card


@router.put("/{card_id}", response_model=FeatureCardResponse)
def update_feature_card(card_id: str, data: FeatureCardUpdate, db: Session = Depends(get_db_sync)):
    """更新功能卡片配置"""
    result = db.execute(select(FeatureCard).where(FeatureCard.id == card_id))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(card, key, value)
    
    db.commit()
    db.refresh(card)
    
    return card


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature_card(card_id: str, db: Session = Depends(get_db_sync)):
    """删除自定义功能卡片"""
    result = db.execute(select(FeatureCard).where(FeatureCard.id == card_id))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Only allow deleting custom cards
    if not card.is_custom:
        raise HTTPException(status_code=400, detail="Cannot delete default cards")
    
    db.delete(card)
    db.commit()
    
    return None


@router.put("/reorder", response_model=FeatureCardListResponse)
def reorder_feature_cards(card_ids: list[str], db: Session = Depends(get_db_sync)):
    """批量更新卡片顺序"""
    for index, card_id in enumerate(card_ids):
        result = db.execute(select(FeatureCard).where(FeatureCard.id == card_id))
        card = result.scalar_one_or_none()
        if card:
            card.sort_order = index
    
    db.commit()
    
    # Return updated list
    result = db.execute(select(FeatureCard).order_by(FeatureCard.sort_order))
    cards = result.scalars().all()
    
    return FeatureCardListResponse(
        items=[FeatureCardResponse.model_validate(card) for card in cards],
        total=len(cards)
    )

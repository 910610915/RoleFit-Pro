from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db_sync
from app.models.sqlite import Position
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse, PositionListResponse

router = APIRouter(prefix="/positions", tags=["Positions"])


@router.get("", response_model=PositionListResponse)
def list_positions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: Optional[str] = None,
    db: Session = Depends(get_db_sync)
):
    """获取岗位列表"""
    query = select(Position).where(Position.is_active == True)
    
    if department:
        query = query.where(Position.department == department)
    
    # Count total
    count_result = db.execute(select(func.count(Position.id)))
    total = count_result.scalar() or 0
    
    # Paginate
    query = query.order_by(Position.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    items = result.scalars().all()
    
    return PositionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[PositionResponse.model_validate(item) for item in items]
    )


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db_sync)
):
    """创建岗位"""
    position = Position(**data.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(
    position_id: str,
    db: Session = Depends(get_db_sync)
):
    """获取岗位详情"""
    result = db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.put("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: str,
    data: PositionUpdate,
    db: Session = Depends(get_db_sync)
):
    """更新岗位"""
    result = db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(position, key, value)
    
    db.commit()
    db.refresh(position)
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: str,
    db: Session = Depends(get_db_sync)
):
    """删除岗位(软删除)"""
    result = db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    position.is_active = False
    db.commit()
    return None

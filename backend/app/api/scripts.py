from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import json

from app.core.database import get_db
from app.models.sqlite import JobScript
from app.schemas.script import ScriptCreate, ScriptUpdate, ScriptResponse, ScriptListResponse

router = APIRouter(prefix="/scripts", tags=["Scripts"])


def script_to_response(script: JobScript) -> dict:
    """转换脚本为响应格式，处理position_ids"""
    result = {}
    for column in script.__table__.columns:
        value = getattr(script, column.name)
        if column.name == 'position_ids' and value:
            try:
                result[column.name] = json.loads(value) if isinstance(value, str) else value
            except:
                result[column.name] = []
        else:
            result[column.name] = value
    return result


@router.get("", response_model=ScriptListResponse)
async def list_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    position_id: Optional[str] = None,
    software_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取岗位测试脚本列表"""
    query = select(JobScript).where(JobScript.is_active == True)
    
    # 处理多岗位筛选
    if position_id:
        # 检查position_id是否在position_ids数组中
        query = query.where(JobScript.position_ids.like(f'%{position_id}%'))
    
    if software_id:
        query = query.where(JobScript.software_id == software_id)
    
    count_result = await db.execute(select(func.count(JobScript.id)))
    total = count_result.scalar() or 0
    
    query = query.order_by(JobScript.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ScriptListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ScriptResponse.model_validate(script_to_response(item)) for item in items]
    )


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def create_script(
    data: ScriptCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建岗位测试脚本"""
    # 转换position_ids为JSON字符串
    script_data = data.model_dump()
    
    # 处理position_ids
    pos_ids = script_data.get('position_ids')
    if pos_ids is not None and isinstance(pos_ids, list):
        script_data['position_ids'] = json.dumps(pos_ids)
    else:
        script_data['position_ids'] = None
    
    script = JobScript(**script_data)
    db.add(script)
    await db.commit()
    await db.refresh(script)
    # 使用 script_to_response 转换响应格式
    return ScriptResponse.model_validate(script_to_response(script))


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取脚本详情"""
    result = await db.execute(select(JobScript).where(JobScript.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script_to_response(script)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: str,
    data: ScriptUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新脚本"""
    result = await db.execute(select(JobScript).where(JobScript.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 转换position_ids为JSON字符串
    if 'position_ids' in update_data:
        if update_data['position_ids']:
            update_data['position_ids'] = json.dumps(update_data['position_ids'])
        else:
            update_data['position_ids'] = '[]'
    
    for key, value in update_data.items():
        setattr(script, key, value)
    
    await db.commit()
    await db.refresh(script)
    # 使用 script_to_response 转换响应格式
    return ScriptResponse.model_validate(script_to_response(script))


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除脚本(软删除)"""
    result = await db.execute(select(JobScript).where(JobScript.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    script.is_active = False
    await db.commit()
    return None

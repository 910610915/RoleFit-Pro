from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.models.sqlite import ScriptExecution
from app.schemas.execution import ExecutionCreate, ExecutionUpdate, ExecutionResponse, ExecutionListResponse

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("", response_model=ExecutionListResponse)
async def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_id: Optional[str] = None,
    script_id: Optional[str] = None,
    device_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """获取脚本执行记录列表"""
    query = select(ScriptExecution)
    
    if task_id:
        query = query.where(ScriptExecution.task_id == task_id)
    if script_id:
        query = query.where(ScriptExecution.script_id == script_id)
    if device_id:
        query = query.where(ScriptExecution.device_id == device_id)
    
    count_result = await db.execute(select(func.count(ScriptExecution.id)))
    total = count_result.scalar() or 0
    
    query = query.order_by(ScriptExecution.start_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ExecutionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ExecutionResponse.model_validate(item) for item in items]
    )


@router.post("", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def create_execution(
    data: ExecutionCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建脚本执行记录"""
    execution = ScriptExecution(
        **data.model_dump(),
        start_time=datetime.utcnow()
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取执行记录详情"""
    result = await db.execute(select(ScriptExecution).where(ScriptExecution.id == execution_id))
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.put("/{execution_id}", response_model=ExecutionResponse)
async def update_execution(
    execution_id: str,
    data: ExecutionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新执行记录(主要用于更新结束时间和状态)"""
    result = await db.execute(select(ScriptExecution).where(ScriptExecution.id == execution_id))
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(execution, key, value)
    
    # 计算执行时长
    if execution.end_time and execution.start_time:
        execution.duration_seconds = int((execution.end_time - execution.start_time).total_seconds())
    
    await db.commit()
    await db.refresh(execution)
    return execution


@router.delete("/{execution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除执行记录"""
    result = await db.execute(select(ScriptExecution).where(ScriptExecution.id == execution_id))
    execution = result.scalar_one_or_none()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    await db.delete(execution)
    await db.commit()
    return None

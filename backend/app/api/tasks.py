from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import uuid
import json

from app.core.database import get_db
from app.models.sqlite import TestTask, TestScript, Device
from app.schemas.task import (
    TestTaskCreate, TestTaskUpdate, TestTaskResponse,
    TestTaskListResponse, TaskExecuteRequest, TaskCancelRequest
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def task_to_response(task: TestTask) -> dict:
    """Convert TestTask model to response dict, parsing JSON fields"""
    result = {}
    for column in task.__table__.columns:
        value = getattr(task, column.name)
        # Parse JSON fields
        if column.name in ['target_device_ids', 'target_departments', 'target_positions'] and value:
            try:
                result[column.name] = json.loads(value)
            except:
                result[column.name] = value
        else:
            result[column.name] = value
    return result


@router.post("", response_model=TestTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TestTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new test task"""
    # Validate script if provided
    if task_data.test_script_id:
        result = await db.execute(
            select(TestScript).where(TestScript.id == task_data.test_script_id)
        )
        script = result.scalar_one_or_none()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Test script not found"
            )
    
    db_task = TestTask(
        task_name=task_data.task_name,
        task_type=task_data.task_type,
        task_status="pending",
        # Convert lists to JSON strings for SQLite
        target_device_ids=json.dumps(task_data.target_device_ids or []),
        target_departments=json.dumps(task_data.target_departments or []),
        target_positions=json.dumps(task_data.target_positions or []),
        test_script_id=task_data.test_script_id,
        test_duration_seconds=task_data.test_duration_seconds,
        sample_interval_ms=task_data.sample_interval_ms,
        schedule_type=task_data.schedule_type,
        scheduled_at=task_data.scheduled_at,
        cron_expression=task_data.cron_expression,
        created_by=None
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    return task_to_response(db_task)


@router.get("", response_model=TestTaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get test task list"""
    query = select(TestTask)
    
    if task_status:
        query = query.where(TestTask.task_status == task_status)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Apply pagination and ordering
    query = query.order_by(TestTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TestTaskListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TestTaskResponse.model_validate(task_to_response(t)) for t in tasks]
    )


@router.get("/{task_id}", response_model=TestTaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task_to_response(task)


@router.put("/{task_id}", response_model=TestTaskResponse)
async def update_task(
    task_id: str,
    task_data: TestTaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update task"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    for key, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    
    await db.commit()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/execute", response_model=TestTaskResponse)
async def execute_task(
    task_id: str,
    request: TaskExecuteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a task"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.task_status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot execute task with status: {task.task_status}"
        )
    
    # Update task status
    task.task_status = "running"
    task.started_at = datetime.utcnow()
    task.target_device_ids = json.dumps(request.device_ids)
    
    await db.commit()
    await db.refresh(task)
    
    # Return updated task
    return task_to_response(task)


@router.post("/{task_id}/cancel", response_model=TestTaskResponse)
async def cancel_task(
    task_id: str,
    request: TaskCancelRequest,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a running task"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.task_status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task with status: {task.task_status}"
        )
    
    task.task_status = "cancelled"
    task.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    
    return task


@router.post("/{task_id}/complete", response_model=TestTaskResponse)
async def complete_task(
    task_id: str,
    task_status: str = Query("completed"),
    db: AsyncSession = Depends(get_db)
):
    """Mark task as completed"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.task_status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete task with status: {task.task_status}"
        )
    
    task.task_status = task_status
    task.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(task)
    
    return task_to_response(task)


# ====== 软件错误上报 ======

class SoftwareErrorRequest(BaseModel):
    error_type: str
    error_message: str
    timestamp: str
    device_id: Optional[str] = None


@router.post("/{task_id}/software_error")
async def report_software_error(
    task_id: str,
    request: SoftwareErrorRequest,
    db: AsyncSession = Depends(get_db)
):
    """Agent上报软件安装/执行错误"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 记录错误信息
    task.task_status = "failed"
    task.completed_at = datetime.utcnow()
    # 将错误信息存储在 notes 字段
    error_info = f"[软件错误] 类型:{request.error_type}, 消息:{request.error_message}, 时间:{request.timestamp}"
    task.notes = (task.notes or '') + '\n' + error_info if task.notes else error_info
    
    await db.commit()
    await db.refresh(task)
    
    return {"status": "error_reported", "message": request.error_message}
    
    return task_to_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete task"""
    result = await db.execute(
        select(TestTask).where(TestTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    await db.delete(task)
    await db.commit()

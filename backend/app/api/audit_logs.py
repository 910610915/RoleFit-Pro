"""
审计日志 API
提供审计日志的查询和管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json

from app.core.database import get_db_sync
from app.models.sqlite import AuditLog, User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime


class AuditLogCreate(BaseModel):
    """创建审计日志请求"""

    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db_sync),
):
    """获取审计日志列表"""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action.like(f"%{action}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count(AuditLog.id))
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        count_query = count_query.where(AuditLog.action.like(f"%{action}%"))
    if resource_type:
        count_query = count_query.where(AuditLog.resource_type == resource_type)
    if start_date:
        count_query = count_query.where(AuditLog.created_at >= start_date)
    if end_date:
        count_query = count_query.where(AuditLog.created_at <= end_date)

    total = db.execute(count_query).scalar() or 0

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    logs = result.scalars().all()

    return [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            old_value=log.old_value,
            new_value=log.new_value,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(log_id: str, db: Session = Depends(get_db_sync)):
    """获取审计日志详情"""
    result = db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="审计日志不存在")

    return AuditLogResponse(
        id=log.id,
        user_id=log.user_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        old_value=log.old_value,
        new_value=log.new_value,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        created_at=log.created_at,
    )


@router.post("", response_model=AuditLogResponse, status_code=201)
def create_audit_log(log_data: AuditLogCreate, db: Session = Depends(get_db_sync)):
    """创建审计日志（通常由系统自动创建）"""
    db_log = AuditLog(
        id=str(uuid.uuid4()),
        user_id=log_data.user_id,
        action=log_data.action,
        resource_type=log_data.resource_type,
        resource_id=log_data.resource_id,
        old_value=json.dumps(log_data.old_value) if log_data.old_value else None,
        new_value=json.dumps(log_data.new_value) if log_data.new_value else None,
        ip_address=log_data.ip_address,
        user_agent=log_data.user_agent,
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return AuditLogResponse(
        id=db_log.id,
        user_id=db_log.user_id,
        action=db_log.action,
        resource_type=db_log.resource_type,
        resource_id=db_log.resource_id,
        old_value=db_log.old_value,
        new_value=db_log.new_value,
        ip_address=db_log.ip_address,
        user_agent=db_log.user_agent,
        created_at=db_log.created_at,
    )


@router.get("/actions/list")
def get_action_types(db: Session = Depends(get_db_sync)):
    """获取所有操作类型"""
    result = db.execute(select(AuditLog.action).distinct().order_by(AuditLog.action))
    actions = [row[0] for row in result.fetchall() if row[0]]
    return {"actions": actions}


@router.get("/resource-types/list")
def get_resource_types(db: Session = Depends(get_db_sync)):
    """获取所有资源类型"""
    result = db.execute(
        select(AuditLog.resource_type).distinct().order_by(AuditLog.resource_type)
    )
    types = [row[0] for row in result.fetchall() if row[0]]
    return {"resource_types": types}


@router.get("/stats/summary")
def get_audit_stats(
    days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db_sync)
):
    """获取审计统计摘要"""
    from datetime import timedelta

    since = datetime.utcnow() - timedelta(days=days)

    # Total count
    total = (
        db.execute(select(AuditLog).where(AuditLog.created_at >= since)).scalars().all()
    )
    total_count = len(total)

    # Count by action
    action_counts = {}
    for log in total:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1

    # Count by resource type
    resource_counts = {}
    for log in total:
        if log.resource_type:
            resource_counts[log.resource_type] = (
                resource_counts.get(log.resource_type, 0) + 1
            )

    return {
        "period_days": days,
        "total_count": total_count,
        "action_counts": dict(
            sorted(action_counts.items(), key=lambda x: x[1], reverse=True)
        ),
        "resource_counts": dict(
            sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)
        ),
    }

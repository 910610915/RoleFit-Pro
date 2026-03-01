"""
告警管理API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, List
from datetime import datetime, timedelta
import json

from app.core.database import get_db_sync
from app.models.sqlite import AlarmRule, Alarm, Device, TestResult
from pydantic import BaseModel

router = APIRouter(prefix="/alarms", tags=["Alarms"])


# ==================== Schemas ====================


class AlarmRuleCreate(BaseModel):
    name: str
    alarm_type: str
    condition: str
    threshold: Optional[float] = None
    enabled: bool = True
    notification_channels: Optional[List[str]] = None


class AlarmRuleResponse(BaseModel):
    id: str
    name: str
    alarm_type: str
    condition: str
    threshold: Optional[float]
    enabled: bool
    notification_channels: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class AlarmResponse(BaseModel):
    id: str
    rule_id: Optional[str]
    device_id: Optional[str]
    alarm_type: str
    severity: str
    title: str
    message: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Alarm Rules ====================


@router.get("/rules", response_model=List[AlarmRuleResponse])
async def list_alarm_rules(
    enabled: Optional[bool] = None, db: AsyncSession = Depends(get_db_sync)
):
    """获取告警规则列表"""
    query = select(AlarmRule).order_by(AlarmRule.created_at.desc())

    if enabled is not None:
        query = query.where(AlarmRule.enabled == enabled)

    result = await db.execute(query)
    rules = result.scalars().all()

    return [
        AlarmRuleResponse(
            id=r.id,
            name=r.name,
            alarm_type=r.alarm_type,
            condition=r.condition,
            threshold=r.threshold,
            enabled=r.enabled,
            notification_channels=json.loads(r.notification_channels)
            if r.notification_channels
            else [],
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post(
    "/rules", response_model=AlarmRuleResponse, status_code=status.HTTP_201_CREATED
)
async def create_alarm_rule(
    rule_data: AlarmRuleCreate, db: AsyncSession = Depends(get_db_sync)
):
    """创建告警规则"""
    db_rule = AlarmRule(
        name=rule_data.name,
        alarm_type=rule_data.alarm_type,
        condition=rule_data.condition,
        threshold=rule_data.threshold,
        enabled=rule_data.enabled,
        notification_channels=json.dumps(rule_data.notification_channels or []),
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)

    return AlarmRuleResponse(
        id=db_rule.id,
        name=db_rule.name,
        alarm_type=db_rule.alarm_type,
        condition=db_rule.condition,
        threshold=db_rule.threshold,
        enabled=db_rule.enabled,
        notification_channels=json.loads(db_rule.notification_channels)
        if db_rule.notification_channels
        else [],
        created_at=db_rule.created_at,
    )


@router.put("/rules/{rule_id}", response_model=AlarmRuleResponse)
async def update_alarm_rule(
    rule_id: str, rule_data: AlarmRuleCreate, db: AsyncSession = Depends(get_db_sync)
):
    """更新告警规则"""
    result = await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.name = rule_data.name
    rule.alarm_type = rule_data.alarm_type
    rule.condition = rule_data.condition
    rule.threshold = rule_data.threshold
    rule.enabled = rule_data.enabled
    rule.notification_channels = json.dumps(rule_data.notification_channels or [])
    rule.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(rule)

    return AlarmRuleResponse(
        id=rule.id,
        name=rule.name,
        alarm_type=rule.alarm_type,
        condition=rule.condition,
        threshold=rule.threshold,
        enabled=rule.enabled,
        notification_channels=json.loads(rule.notification_channels)
        if rule.notification_channels
        else [],
        created_at=rule.created_at,
    )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alarm_rule(rule_id: str, db: AsyncSession = Depends(get_db_sync)):
    """删除告警规则"""
    result = await db.execute(select(AlarmRule).where(AlarmRule.id == rule_id))
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()

    return None


# ==================== Alarms ====================


@router.get("", response_model=List[AlarmResponse])
async def list_alarms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_resolved: Optional[bool] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db_sync),
):
    """获取告警列表"""
    query = select(Alarm).order_by(Alarm.created_at.desc())

    if is_resolved is not None:
        query = query.where(Alarm.is_resolved == is_resolved)
    if severity:
        query = query.where(Alarm.severity == severity)

    count_result = await db.execute(select(func.count(Alarm.id)))
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    alarms = result.scalars().all()

    return [
        AlarmResponse(
            id=a.id,
            rule_id=a.rule_id,
            device_id=a.device_id,
            alarm_type=a.alarm_type,
            severity=a.severity,
            title=a.title,
            message=a.message,
            is_resolved=a.is_resolved,
            resolved_at=a.resolved_at,
            created_at=a.created_at,
        )
        for a in alarms
    ]


@router.post("/{alarm_id}/resolve", response_model=AlarmResponse)
async def resolve_alarm(alarm_id: str, db: AsyncSession = Depends(get_db_sync)):
    """解决告警"""
    result = await db.execute(select(Alarm).where(Alarm.id == alarm_id))
    alarm = result.scalar_one_or_none()

    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm.is_resolved = True
    alarm.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(alarm)

    return AlarmResponse(
        id=alarm.id,
        rule_id=alarm.rule_id,
        device_id=alarm.device_id,
        alarm_type=alarm.alarm_type,
        severity=alarm.severity,
        title=alarm.title,
        message=alarm.message,
        is_resolved=alarm.is_resolved,
        resolved_at=alarm.resolved_at,
        created_at=alarm.created_at,
    )


# ==================== Alarm Check ====================


@router.post("/check")
async def check_alarms(db: AsyncSession = Depends(get_db_sync)):
    """手动触发告警检查"""
    checked_count = 0

    # 1. 检查离线设备
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    offline_query = select(Device).where(
        and_(Device.status == "offline", Device.last_seen_at < cutoff)
    )
    result = await db.execute(offline_query)
    offline_devices = result.scalars().all()

    for device in offline_devices:
        # 检查是否已有未解决的离线告警
        existing = await db.execute(
            select(Alarm).where(
                and_(
                    Alarm.device_id == device.id,
                    Alarm.alarm_type == "device_offline",
                    Alarm.is_resolved == False,
                )
            )
        )
        if not existing.scalar_one_or_none():
            alarm = Alarm(
                device_id=device.id,
                alarm_type="device_offline",
                severity="error",
                title=f"设备离线: {device.device_name}",
                message=f"设备 {device.device_name} 已离线超过10分钟",
            )
            db.add(alarm)
            checked_count += 1

    # 2. 检查失败的测试
    failed_query = select(TestResult).where(
        and_(
            TestResult.test_status == "failed",
            TestResult.start_time >= datetime.utcnow() - timedelta(hours=1),
        )
    )
    result = await db.execute(failed_query)
    failed_tests = result.scalars().all()

    for test in failed_tests:
        existing = await db.execute(
            select(Alarm).where(
                and_(
                    Alarm.device_id == test.device_id,
                    Alarm.alarm_type == "test_failed",
                    Alarm.is_resolved == False,
                )
            )
        )
        if not existing.scalar_one_or_none():
            alarm = Alarm(
                device_id=test.device_id,
                alarm_type="test_failed",
                severity="warning",
                title=f"测试失败",
                message=f"设备测试失败，类型: {test.test_type}",
            )
            db.add(alarm)
            checked_count += 1

    await db.commit()

    return {
        "checked": checked_count,
        "message": f"检查完成，发现 {checked_count} 个新告警",
    }

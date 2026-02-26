from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.sqlite import Device, TestResult, TestTask, PositionStandard
from pydantic import BaseModel

router = APIRouter(prefix="/stats", tags=["Statistics"])


# Response schemas
class DashboardSummary(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    testing_devices: int
    total_tasks: int
    pending_tasks: int
    running_tasks: int
    completed_tasks: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_score: float


class DeviceStatusDistribution(BaseModel):
    online: int
    offline: int
    testing: int
    error: int


class DepartmentDeviceCount(BaseModel):
    department: str
    count: int
    online_count: int
    average_score: Optional[float]


class ScoreTrend(BaseModel):
    date: str
    average_score: float
    test_count: int


class PositionCompliance(BaseModel):
    position: str
    total_devices: int
    compliant_devices: int
    compliance_rate: float


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard summary statistics"""
    
    # Device counts
    device_result = await db.execute(select(func.count(Device.id)))
    total_devices = device_result.scalar() or 0
    
    online_result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "online")
    )
    online_devices = online_result.scalar() or 0
    
    offline_result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "offline")
    )
    offline_devices = offline_result.scalar() or 0
    
    testing_result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "testing")
    )
    testing_devices = testing_result.scalar() or 0
    
    # Task counts
    task_result = await db.execute(select(func.count(TestTask.id)))
    total_tasks = task_result.scalar() or 0
    
    pending_result = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.task_status == "pending")
    )
    pending_tasks = pending_result.scalar() or 0
    
    running_result = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.task_status == "running")
    )
    running_tasks = running_result.scalar() or 0
    
    completed_result = await db.execute(
        select(func.count(TestTask.id)).where(TestTask.task_status == "completed")
    )
    completed_tasks = completed_result.scalar() or 0
    
    # Test counts
    test_result = await db.execute(select(func.count(TestResult.id)))
    total_tests = test_result.scalar() or 0
    
    passed_result = await db.execute(
        select(func.count(TestResult.id)).where(TestResult.test_status == "passed")
    )
    passed_tests = passed_result.scalar() or 0
    
    failed_result = await db.execute(
        select(func.count(TestResult.id)).where(TestResult.test_status == "failed")
    )
    failed_tests = failed_result.scalar() or 0
    
    # Average score
    score_result = await db.execute(
        select(func.avg(TestResult.overall_score))
    )
    average_score = float(score_result.scalar() or 0)
    
    return DashboardSummary(
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=offline_devices,
        testing_devices=testing_devices,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        average_score=average_score
    )


@router.get("/devices/status-distribution", response_model=DeviceStatusDistribution)
async def get_device_status_distribution(db: AsyncSession = Depends(get_db)):
    """Get device status distribution"""
    
    # Online count
    result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "online")
    )
    online = result.scalar() or 0
    
    # Offline count
    result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "offline")
    )
    offline = result.scalar() or 0
    
    # Testing count
    result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "testing")
    )
    testing = result.scalar() or 0
    
    # Error count
    result = await db.execute(
        select(func.count(Device.id)).where(Device.status == "error")
    )
    error = result.scalar() or 0
    
    return DeviceStatusDistribution(
        online=online,
        offline=offline,
        testing=testing,
        error=error
    )


@router.get("/devices/by-department", response_model=List[DepartmentDeviceCount])
async def get_devices_by_department(db: AsyncSession = Depends(get_db)):
    """Get device counts by department"""
    
    # Get unique departments
    result = await db.execute(
        select(Device.department).where(Device.department.isnot(None)).distinct()
    )
    departments = [r[0] for r in result.all() if r[0]]
    
    dept_counts = []
    for dept in departments:
        # Total count
        count_result = await db.execute(
            select(func.count(Device.id)).where(Device.department == dept)
        )
        count = count_result.scalar() or 0
        
        # Online count
        online_result = await db.execute(
            select(func.count(Device.id)).where(
                and_(Device.department == dept, Device.status == "online")
            )
        )
        online_count = online_result.scalar() or 0
        
        # Average score from latest results - fixed join
        score_result = await db.execute(
            select(func.avg(TestResult.overall_score))
            .select_from(TestResult)
            .join(Device, TestResult.device_id == Device.id)
            .where(Device.department == dept)
        )
        score_row = score_result.scalar()
        avg_score = float(score_row) if score_row else None
        
        dept_counts.append(DepartmentDeviceCount(
            department=dept,
            count=count,
            online_count=online_count,
            average_score=avg_score
        ))
    
    return dept_counts


@router.get("/scores/trend", response_model=List[ScoreTrend])
async def get_score_trend(
    days: int = Query(30, ge=7, le=90),
    db: AsyncSession = Depends(get_db)
):
    """Get score trend over time"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily statistics
    result = await db.execute(
        select(TestResult).where(TestResult.start_time >= start_date)
    )
    results = result.scalars().all()
    
    # Group by date
    daily_stats = {}
    for r in results:
        date_key = r.start_time.strftime("%Y-%m-%d")
        if date_key not in daily_stats:
            daily_stats[date_key] = {"scores": [], "count": 0}
        if r.overall_score:
            daily_stats[date_key]["scores"].append(r.overall_score)
        daily_stats[date_key]["count"] += 1
    
    # Convert to trend list
    trend = []
    for date_key in sorted(daily_stats.keys()):
        stats = daily_stats[date_key]
        avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
        trend.append(ScoreTrend(
            date=date_key,
            average_score=round(avg_score, 2),
            test_count=stats["count"]
        ))
    
    return trend


@router.get("/positions/compliance", response_model=List[PositionCompliance])
async def get_position_compliance(db: AsyncSession = Depends(get_db)):
    """Get compliance rate by position"""
    
    # Get unique positions
    result = await db.execute(
        select(Device.position).where(Device.position.isnot(None)).distinct()
    )
    positions = [r[0] for r in result.all() if r[0]]
    
    compliance_list = []
    for pos in positions:
        # Total devices with this position
        total_result = await db.execute(
            select(func.count(Device.id)).where(Device.position == pos)
        )
        total = total_result.scalar() or 0
        
        if total == 0:
            continue
        
        # Count distinct devices that passed standards (at least one passing test result)
        compliant_result = await db.execute(
            select(func.count(func.distinct(TestResult.device_id)))
            .join(Device, TestResult.device_id == Device.id)
            .where(
                and_(
                    Device.position == pos,
                    TestResult.is_standard_met == True
                )
            )
        )
        compliant = compliant_result.scalar() or 0
        
        compliance_list.append(PositionCompliance(
            position=pos,
            total_devices=total,
            compliant_devices=compliant,
            compliance_rate=round(compliant / total * 100, 2) if total > 0 else 0
        ))
    
    return compliance_list


@router.get("/leaderboard/devices", response_model=List[Dict[str, Any]])
async def get_device_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get top performing devices"""
    
    result = await db.execute(
        select(Device, TestResult.overall_score)
        .join(TestResult, Device.id == TestResult.device_id)
        .order_by(TestResult.overall_score.desc())
        .limit(limit)
    )
    
    leaderboard = []
    for device, score in result.all():
        leaderboard.append({
            "device_id": str(device.id),
            "device_name": device.device_name,
            "score": score,
            "cpu": device.cpu_model,
            "gpu": device.gpu_model
        })
    
    return leaderboard

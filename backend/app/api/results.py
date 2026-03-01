from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db_sync
from app.models.sqlite import (
    TestResult,
    Device,
    TestTask,
    PositionStandard,
    ScriptExecution,
    SoftwareMetrics,
)
from app.schemas.result import (
    TestResultCreate,
    TestResultUpdate,
    TestResultResponse,
    TestResultListResponse,
    ResultStatistics,
    DevicePerformanceSummary,
)

router = APIRouter(prefix="/results", tags=["Results"])


@router.post("", response_model=TestResultResponse, status_code=status.HTTP_201_CREATED)
async def create_result(
    result_data: TestResultCreate, db: AsyncSession = Depends(get_db_sync)
):
    """Create a new test result"""
    # Verify device exists
    result = await db.execute(select(Device).where(Device.id == result_data.device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    db_result = TestResult(
        task_id=result_data.task_id,
        device_id=result_data.device_id,
        test_type=result_data.test_type,
        test_status=result_data.test_status,
        start_time=result_data.start_time,
        end_time=result_data.end_time,
        duration_seconds=result_data.duration_seconds,
    )
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)

    return db_result


@router.get("", response_model=TestResultListResponse)
async def list_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    test_status: Optional[str] = None,
    device_id: Optional[str] = None,
    task_id: Optional[str] = None,
    is_standard_met: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db_sync),
):
    """Get test result list"""
    query = select(TestResult)

    if device_id:
        query = query.where(TestResult.device_id == device_id)
    if task_id:
        query = query.where(TestResult.task_id == task_id)
    if test_status:
        query = query.where(TestResult.test_status == test_status)
    if is_standard_met is not None:
        query = query.where(TestResult.is_standard_met == is_standard_met)
    if start_date:
        query = query.where(TestResult.start_time >= start_date)
    if end_date:
        query = query.where(TestResult.start_time <= end_date)

    # Count total - simplified query
    count_result = await db.execute(select(func.count(TestResult.id)))
    total = count_result.scalar() or 0

    # Apply pagination and ordering
    query = (
        query.order_by(TestResult.start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    results = result.scalars().all()

    return TestResultListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TestResultResponse.model_validate(r) for r in results],
    )


# ==================== 设备对比 (必须在 /{result_id} 前面) ====================


@router.get("/compare", response_model=List[dict])
async def compare_devices(
    device_ids: str = Query(..., description="设备ID列表，用逗号分隔"),
    db: AsyncSession = Depends(get_db_sync),
):
    """对比多台设备的性能"""
    device_id_list = [d.strip() for d in device_ids.split(",") if d.strip()]

    if not device_id_list:
        return []

    comparison = []

    for device_id in device_id_list:
        # 获取设备信息
        device_result = await db.execute(select(Device).where(Device.id == device_id))
        device = device_result.scalar_one_or_none()

        if not device:
            continue

        # 获取该设备的最新测试结果
        result_query = (
            select(TestResult)
            .where(TestResult.device_id == device_id)
            .order_by(TestResult.start_time.desc())
            .limit(1)
        )

        result = await db.execute(result_query)
        latest_result = result.scalar_one_or_none()

        # 获取历史测试统计
        stats_query = select(
            func.avg(TestResult.overall_score).label("avg_score"),
            func.max(TestResult.overall_score).label("max_score"),
            func.min(TestResult.overall_score).label("min_score"),
            func.count(TestResult.id).label("test_count"),
        ).where(TestResult.device_id == device_id)

        stats_result = await db.execute(stats_query)
        stats = stats_result.first()

        # 计算综合分数 = 4项平均
        calculated_overall = None
        if (
            latest_result
            and latest_result.cpu_score
            and latest_result.gpu_score
            and latest_result.memory_score
            and latest_result.disk_score
        ):
            calculated_overall = (
                latest_result.cpu_score
                + latest_result.gpu_score
                + latest_result.memory_score
                + latest_result.disk_score
            ) / 4

        comparison.append(
            {
                "device_id": device.id,
                "device_name": device.device_name,
                "cpu_model": device.cpu_model,
                "gpu_model": device.gpu_model,
                "ram_total_gb": device.ram_total_gb,
                "latest_result": {
                    "overall_score": latest_result.overall_score
                    if latest_result
                    else None,
                    "calculated_overall": calculated_overall,
                    "cpu_score": latest_result.cpu_score if latest_result else None,
                    "gpu_score": latest_result.gpu_score if latest_result else None,
                    "memory_score": latest_result.memory_score
                    if latest_result
                    else None,
                    "disk_score": latest_result.disk_score if latest_result else None,
                    "test_status": latest_result.test_status if latest_result else None,
                    "test_time": latest_result.start_time.isoformat()
                    if latest_result and latest_result.start_time
                    else None,
                }
                if latest_result
                else None,
                "statistics": {
                    "average_score": float(stats.avg_score)
                    if stats.avg_score
                    else None,
                    "max_score": float(stats.max_score) if stats.max_score else None,
                    "min_score": float(stats.min_score) if stats.min_score else None,
                    "test_count": stats.test_count if stats else 0,
                },
            }
        )

    return comparison


@router.get("/{result_id}", response_model=TestResultResponse)
async def get_result(result_id: str, db: AsyncSession = Depends(get_db_sync)):
    """Get result details"""
    result = await db.execute(select(TestResult).where(TestResult.id == result_id))
    test_result = result.scalar_one_or_none()

    if not test_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Result not found"
        )

    return test_result


@router.put("/{result_id}", response_model=TestResultResponse)
async def update_result(
    result_id: str,
    result_data: TestResultUpdate,
    db: AsyncSession = Depends(get_db_sync),
):
    """Update result"""
    result = await db.execute(select(TestResult).where(TestResult.id == result_id))
    test_result = result.scalar_one_or_none()

    if not test_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Result not found"
        )

    for key, value in result_data.model_dump(exclude_unset=True).items():
        setattr(test_result, key, value)

    await db.commit()
    await db.refresh(test_result)

    return test_result


@router.get("/statistics/overview", response_model=ResultStatistics)
async def get_overall_statistics(
    days: int = Query(30, ge=1, le=365), db: AsyncSession = Depends(get_db_sync)
):
    """Get overall test statistics"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Query results within date range
    query = select(TestResult).where(TestResult.start_time >= start_date)
    result = await db.execute(query)
    results = result.scalars().all()

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.test_status == "passed")
    failed_tests = sum(1 for r in results if r.test_status == "failed")
    warning_tests = sum(1 for r in results if r.test_status == "warning")

    # Calculate averages
    scores = [r.overall_score for r in results if r.overall_score]
    average_score = sum(scores) / len(scores) if scores else 0

    cpu_scores = [r.cpu_score for r in results if r.cpu_score]
    average_cpu = sum(cpu_scores) / len(cpu_scores) if cpu_scores else 0

    gpu_scores = [r.gpu_score for r in results if r.gpu_score]
    average_gpu = sum(gpu_scores) / len(gpu_scores) if gpu_scores else 0

    memory_scores = [r.memory_score for r in results if r.memory_score]
    average_memory = sum(memory_scores) / len(memory_scores) if memory_scores else 0

    disk_scores = [r.disk_score for r in results if r.disk_score]
    average_disk = sum(disk_scores) / len(disk_scores) if disk_scores else 0

    # Standard compliance
    standard_met = [r.is_standard_met for r in results if r.is_standard_met is not None]
    compliance_rate = sum(standard_met) / len(standard_met) * 100 if standard_met else 0

    # Bottleneck counts
    bottlenecks = {}
    for r in results:
        if r.bottleneck_type:
            bottlenecks[r.bottleneck_type] = bottlenecks.get(r.bottleneck_type, 0) + 1

    return ResultStatistics(
        total_tests=total_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        warning_tests=warning_tests,
        average_score=average_score,
        average_cpu_score=average_cpu,
        average_gpu_score=average_gpu,
        average_memory_score=average_memory,
        average_disk_score=average_disk,
        standard_compliance_rate=compliance_rate,
        top_bottlenecks=bottlenecks,
    )


@router.get("/statistics/device/{device_id}", response_model=DevicePerformanceSummary)
async def get_device_performance(
    device_id: str, db: AsyncSession = Depends(get_db_sync)
):
    """Get device performance summary"""
    # Get device
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Get all results for device
    query = (
        select(TestResult)
        .where(TestResult.device_id == device_id)
        .order_by(TestResult.start_time.desc())
    )

    result = await db.execute(query)
    results = result.scalars().all()

    if not results:
        return DevicePerformanceSummary(
            device_id=device_id,
            device_name=device.device_name,
            total_tests=0,
            latest_score=None,
            average_score=None,
            trend=None,
            last_test_time=None,
        )

    total_tests = len(results)
    scores = [r.overall_score for r in results if r.overall_score]
    latest_score = results[0].overall_score if results[0].overall_score else None
    average_score = sum(scores) / len(scores) if scores else None

    # Calculate trend (simple: compare first half average to second half average)
    trend = "stable"
    if len(scores) >= 4:
        mid = len(scores) // 2
        first_half_avg = sum(scores[:mid]) / mid
        second_half_avg = sum(scores[mid:]) / (len(scores) - mid)
        if second_half_avg > first_half_avg * 1.05:
            trend = "improving"
        elif second_half_avg < first_half_avg * 0.95:
            trend = "declining"

    return DevicePerformanceSummary(
        device_id=device_id,
        device_name=device.device_name,
        total_tests=total_tests,
        latest_score=latest_score,
        average_score=average_score,
        trend=trend,
        last_test_time=results[0].start_time,
    )


# ==================== 性能指标历史数据 ====================


@router.get("/{result_id}/metrics", response_model=List[dict])
async def get_result_metrics(result_id: str, db: AsyncSession = Depends(get_db_sync)):
    """获取测试结果的性能指标历史数据"""
    # 查找对应的执行记录
    exec_result = await db.execute(
        select(ScriptExecution).where(ScriptExecution.task_id == result_id)
    )
    execution = exec_result.scalar_one_or_none()

    if not execution:
        # 尝试通过其他方式查找
        exec_result = await db.execute(
            select(ScriptExecution).where(
                ScriptExecution.task_id.like(f"%{result_id}%")
            )
        )
        execution = exec_result.scalar_one_or_none()

    if not execution:
        return []

    # 获取指标数据
    metrics_result = await db.execute(
        select(SoftwareMetrics)
        .where(SoftwareMetrics.execution_id == execution.id)
        .order_by(SoftwareMetrics.timestamp.asc())
    )
    metrics = metrics_result.scalars().all()

    return [
        {
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "cpu_percent": m.cpu_percent,
            "memory_mb": m.memory_mb,
            "gpu_percent": m.gpu_percent,
            "gpu_memory_mb": m.gpu_memory_mb,
            "disk_read_mbps": m.disk_read_mbps,
            "disk_write_mbps": m.disk_write_mbps,
            "fps": m.fps,
            "latency_ms": m.latency_ms,
            "status": m.status,
        }
        for m in metrics
    ]

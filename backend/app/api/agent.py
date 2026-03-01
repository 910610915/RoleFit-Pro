"""
Agent API - 用于Agent获取任务和上报结果
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db_sync
from app.models.sqlite import (
    JobScript,
    ScriptExecution,
    TestTask,
    TestSoftware,
    Device,
    SoftwareMetrics,
)
from app.schemas.script import ScriptResponse
from app.schemas.execution import ExecutionCreate, ExecutionResponse

router = APIRouter(tags=["Agent"])


# ==================== 设备相关 ====================


@router.get("/devices/online")
async def get_online_devices(db: AsyncSession = Depends(get_db_sync)):
    """获取在线设备列表"""
    # 5分钟内有心跳的设备视为在线
    cutoff = datetime.utcnow() - timedelta(minutes=5)

    query = select(Device).where(
        and_(Device.status == "online", Device.last_seen_at >= cutoff)
    )
    result = await db.execute(query)
    devices = result.scalars().all()

    return [
        {
            "id": d.id,
            "device_name": d.device_name,
            "hostname": d.hostname,
            "ip_address": d.ip_address,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
        }
        for d in devices
    ]


# ==================== 任务获取 ====================


@router.get("/tasks/pending", response_model=List[dict])
async def get_pending_tasks(
    device_id: str = Query(..., description="设备ID"),
    db: AsyncSession = Depends(get_db_sync),
):
    """
    获取设备待执行的任务
    Agent 轮询此接口获取需要执行的测试任务
    """
    import json

    # 查找分配给该设备的pending状态的任务
    # 或者分配给该部门/岗位的pending任务
    query = select(TestTask).where(TestTask.task_status == "pending")
    result = await db.execute(query)
    tasks = result.scalars().all()

    # 检查设备是否在线
    device_result = await db.execute(select(Device).where(Device.id == device_id))
    device = device_result.scalar_one_or_none()

    response = []
    for task in tasks:
        # 解析目标设备
        target_devices = []
        try:
            target_devices = (
                json.loads(task.target_device_ids) if task.target_device_ids else []
            )
        except:
            pass

        # 检查任务是否分配给该设备
        if device_id in target_devices or not target_devices:
            # 返回任务信息
            response.append(
                {
                    "task_id": task.id,
                    "task_name": task.task_name,
                    "task_type": task.task_type,
                    "test_duration_seconds": task.test_duration_seconds,
                    "sample_interval_ms": task.sample_interval_ms,
                    "target_device_ids": target_devices,
                }
            )

    return response


# ==================== 执行记录 ====================


@router.post("/executions/start", response_model=dict)
async def start_execution(
    script_id: str,
    device_id: str,
    task_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_sync),
):
    """
    Agent 开始执行脚本时调用
    创建执行记录
    """
    execution = ScriptExecution(
        task_id=task_id,
        script_id=script_id,
        device_id=device_id,
        start_time=datetime.utcnow(),
        exit_code=-1,  # 初始值，表示未完成
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    return {
        "execution_id": execution.id,
        "start_time": execution.start_time.isoformat(),
    }


@router.put("/executions/{execution_id}/complete", response_model=dict)
async def complete_execution(
    execution_id: str,
    exit_code: int = Body(0),
    error_message: Optional[str] = Body(None),
    metrics_data: Optional[List[dict]] = Body(None),
    db: AsyncSession = Depends(get_db_sync),
):
    """
    Agent 完成脚本执行时调用
    更新执行记录和性能指标
    """
    result = await db.execute(
        select(ScriptExecution).where(ScriptExecution.id == execution_id)
    )
    execution = result.scalar_one_or_none()

    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution.end_time = datetime.utcnow()
    execution.exit_code = exit_code
    execution.error_message = error_message

    if execution.start_time:
        execution.duration_seconds = int(
            (execution.end_time - execution.start_time).total_seconds()
        )

    await db.commit()

    # 保存性能指标数据
    if metrics_data:
        for m in metrics_data:
            metric = SoftwareMetrics(
                execution_id=execution_id,
                timestamp=datetime.fromisoformat(
                    m.get("timestamp", datetime.utcnow().isoformat())
                ),
                software_name=m.get("software_name"),
                process_id=m.get("process_id"),
                cpu_percent=m.get("cpu_percent"),
                memory_mb=m.get("memory_mb"),
                gpu_percent=m.get("gpu_percent"),
                gpu_memory_mb=m.get("gpu_memory_mb"),
                disk_read_mbps=m.get("disk_read_mbps"),
                disk_write_mbps=m.get("disk_write_mbps"),
                status="completed" if exit_code == 0 else "failed",
            )
            db.add(metric)
        await db.commit()

    return {
        "execution_id": execution.id,
        "success": exit_code == 0,
        "duration_seconds": execution.duration_seconds,
    }


@router.post("/executions/{execution_id}/metrics", response_model=dict)
async def submit_metrics(
    execution_id: str, metrics: List[dict], db: AsyncSession = Depends(get_db_sync)
):
    """
    Agent 实时上报性能指标
    """
    for m in metrics:
        metric = SoftwareMetrics(
            execution_id=execution_id,
            timestamp=datetime.fromisoformat(
                m.get("timestamp", datetime.utcnow().isoformat())
            ),
            software_name=m.get("software_name"),
            process_id=m.get("process_id"),
            cpu_percent=m.get("cpu_percent"),
            memory_mb=m.get("memory_mb"),
            gpu_percent=m.get("gpu_percent"),
            gpu_memory_mb=m.get("gpu_memory_mb"),
            disk_read_mbps=m.get("disk_read_mbps"),
            disk_write_mbps=m.get("disk_write_mbps"),
            fps=m.get("fps"),
            latency_ms=m.get("latency_ms"),
            status="running",
        )
        db.add(metric)

    await db.commit()

    return {"success": True, "count": len(metrics)}


# ==================== 脚本查询 ====================


@router.get("/scripts/{script_id}", response_model=ScriptResponse)
async def get_script_detail(script_id: str, db: AsyncSession = Depends(get_db_sync)):
    """获取脚本详情"""
    result = await db.execute(select(JobScript).where(JobScript.id == script_id))
    script = result.scalar_one_or_none()

    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    return script

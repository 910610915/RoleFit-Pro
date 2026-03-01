"""
调度器 API
提供任务调度管理和状态查询接口
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional, List
from pydantic import BaseModel

from app.services.scheduler_service import scheduler

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


class SchedulerJobResponse(BaseModel):
    """调度任务响应"""

    id: str
    name: str
    next_run_time: Optional[str] = None


class SchedulerStatusResponse(BaseModel):
    """调度器状态响应"""

    running: bool
    jobs: List[SchedulerJobResponse]


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status():
    """获取调度器状态"""
    jobs = scheduler.get_scheduled_jobs()
    return SchedulerStatusResponse(
        running=scheduler._scheduler.running if scheduler._scheduler else False,
        jobs=[SchedulerJobResponse(**job) for job in jobs],
    )


@router.get("/jobs", response_model=List[SchedulerJobResponse])
async def list_jobs():
    """获取所有已调度的任务"""
    jobs = scheduler.get_scheduled_jobs()
    return [SchedulerJobResponse(**job) for job in jobs]


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """获取指定任务详情"""
    job = scheduler.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )
    return job


@router.post("/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """暂停指定任务"""
    try:
        scheduler._scheduler.pause_job(job_id)
        return {"status": "paused", "job_id": job_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to pause job: {str(e)}",
        )


@router.post("/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """恢复指定任务"""
    try:
        scheduler._scheduler.resume_job(job_id)
        return {"status": "resumed", "job_id": job_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resume job: {str(e)}",
        )


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """立即执行指定任务"""
    try:
        job = scheduler._scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
            )

        # 获取任务ID（从 job_id 中提取，格式: task_{task_id}）
        if job_id.startswith("task_"):
            task_id = job_id[5:]
            await scheduler._execute_scheduled_task(task_id)
            return {"status": "executed", "job_id": job_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid job ID format"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to run job: {str(e)}",
        )


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str):
    """移除指定任务"""
    try:
        scheduler._scheduler.remove_job(job_id)
        return {"status": "removed", "job_id": job_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to remove job: {str(e)}",
        )

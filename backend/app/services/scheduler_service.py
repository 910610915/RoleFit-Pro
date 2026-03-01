"""
任务调度服务
负责自动执行定时任务和循环任务
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from sqlalchemy import select, and_

from app.core.database import SyncSessionLocal
from app.models.sqlite import TestTask, ControlCommand, Device

logger = logging.getLogger(__name__)


class TaskScheduler:
    """任务调度器"""

    _instance: Optional["TaskScheduler"] = None
    _scheduler: Optional[AsyncIOScheduler] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._scheduler = AsyncIOScheduler()
            self._initialized = True
            self._setup_event_listeners()

    def _setup_event_listeners(self):
        """设置事件监听器"""

        def job_executed(event):
            if event.exception:
                logger.error(f"Job {event.job_id} failed: {event.exception}")
            else:
                logger.info(f"Job {event.job_id} executed successfully")

        self._scheduler.add_listener(job_executed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    async def start(self):
        """启动调度器"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Task scheduler started")

            # 加载待执行的定时任务
            await self.load_pending_tasks()

    async def stop(self):
        """停止调度器"""
        if self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("Task scheduler stopped")

    async def load_pending_tasks(self):
        """加载并调度所有待执行的定时任务"""
        with SyncSessionLocal() as db:
            # 获取所有 pending 状态且有调度时间的任务
            result = db.execute(
                select(TestTask).where(
                    and_(
                        TestTask.task_status == "pending",
                        TestTask.scheduled_at.isnot(None),
                    )
                )
            )
            tasks = result.scalars().all()

            for task in tasks:
                await self.schedule_task(task)

            logger.info(f"Loaded {len(tasks)} pending scheduled tasks")

    async def schedule_task(self, task: TestTask) -> bool:
        """
        调度一个任务

        Args:
            task: TestTask 实例

        Returns:
            是否成功调度
        """
        try:
            job_id = f"task_{task.id}"

            # 如果任务已存在，先移除
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)

            if task.schedule_type == "once":
                # 一次性任务
                if task.scheduled_at and task.scheduled_at > datetime.utcnow():
                    trigger = DateTrigger(run_date=task.scheduled_at)
                    self._scheduler.add_job(
                        self._execute_scheduled_task,
                        trigger=trigger,
                        args=[task.id],
                        id=job_id,
                        name=task.task_name,
                    )
                    logger.info(
                        f"Scheduled one-time task: {task.task_name} at {task.scheduled_at}"
                    )
                else:
                    # 如果时间已过，立即执行
                    await self._execute_scheduled_task(task.id)

            elif task.schedule_type == "daily":
                # 每日任务
                if task.scheduled_at:
                    trigger = IntervalTrigger(days=1, start_date=task.scheduled_at)
                    self._scheduler.add_job(
                        self._execute_scheduled_task,
                        trigger=trigger,
                        args=[task.id],
                        id=job_id,
                        name=task.task_name,
                    )
                    logger.info(f"Scheduled daily task: {task.task_name}")

            elif task.schedule_type == "weekly":
                # 每周任务
                if task.scheduled_at:
                    trigger = IntervalTrigger(weeks=1, start_date=task.scheduled_at)
                    self._scheduler.add_job(
                        self._execute_scheduled_task,
                        trigger=trigger,
                        args=[task.id],
                        id=job_id,
                        name=task.task_name,
                    )
                    logger.info(f"Scheduled weekly task: {task.task_name}")

            elif task.schedule_type == "cron" and task.cron_expression:
                # Cron 表达式任务
                try:
                    # 简单解析 cron 表达式
                    # 格式: minute hour day month day_of_week
                    parts = task.cron_expression.split()
                    if len(parts) >= 5:
                        trigger = CronTrigger(
                            minute=parts[0],
                            hour=parts[1],
                            day=parts[2],
                            month=parts[3],
                            day_of_week=parts[4],
                        )
                        self._scheduler.add_job(
                            self._execute_scheduled_task,
                            trigger=trigger,
                            args=[task.id],
                            id=job_id,
                            name=task.task_name,
                        )
                        logger.info(
                            f"Scheduled cron task: {task.task_name} ({task.cron_expression})"
                        )
                except Exception as e:
                    logger.error(f"Failed to parse cron expression: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to schedule task {task.id}: {e}")
            return False

    async def _execute_scheduled_task(self, task_id: str):
        """
        执行已调度的任务

        这是实际执行任务的回调函数
        """
        logger.info(f"Executing scheduled task: {task_id}")

        with SyncSessionLocal() as db:
            # 获取任务
            result = db.execute(select(TestTask).where(TestTask.id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.error(f"Task not found: {task_id}")
                return

            # 检查任务状态
            if task.task_status not in ["pending", "scheduled"]:
                logger.warning(
                    f"Task {task_id} status is {task.task_status}, skipping execution"
                )
                return

            # 解析目标设备
            target_devices = []
            if task.target_device_ids:
                try:
                    target_devices = json.loads(task.target_device_ids)
                except:
                    pass

            # 如果没有指定设备，获取所有在线设备
            if not target_devices:
                result = db.execute(select(Device).where(Device.status == "online"))
                devices = result.scalars().all()
                target_devices = [d.id for d in devices]

            # 更新任务状态为 running
            task.task_status = "running"
            task.started_at = datetime.utcnow()
            await db.commit()

            # 为每个目标设备创建控制命令
            for device_id in target_devices:
                command = ControlCommand(
                    device_id=device_id,
                    command_type="start_benchmark",
                    command_params=json.dumps(
                        {
                            "task_id": task.id,
                            "task_type": task.task_type,
                            "test_script_id": task.test_script_id,
                            "schedule_type": task.schedule_type,
                        }
                    ),
                    status="pending",
                    source="scheduler",
                    triggered_by=f"scheduled_task_{task.id}",
                )
                db.add(command)

            await db.commit()
            logger.info(
                f"Task {task_id} executed, commands sent to {len(target_devices)} devices"
            )

    async def cancel_scheduled_task(self, task_id: str) -> bool:
        """
        取消已调度的任务

        Args:
            task_id: 任务 ID

        Returns:
            是否成功取消
        """
        job_id = f"task_{task_id}"

        try:
            if self._scheduler.get_job(job_id):
                self._scheduler.remove_job(job_id)
                logger.info(f"Cancelled scheduled task: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

    def get_scheduled_jobs(self) -> list:
        """获取所有已调度的任务"""
        if not self._scheduler:
            return []

        jobs = []
        for job in self._scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time)
                    if job.next_run_time
                    else None,
                }
            )
        return jobs

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取指定任务"""
        job = self._scheduler.get_job(job_id)
        if job:
            return {
                "id": job.id,
                "name": job.name,
                "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            }
        return None


# 全局调度器实例
scheduler = TaskScheduler()


async def init_scheduler():
    """初始化并启动调度器"""
    await scheduler.start()


async def stop_scheduler():
    """停止调度器"""
    await scheduler.stop()

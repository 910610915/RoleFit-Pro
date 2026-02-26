"""
定时任务调度器
用于处理定时和循环任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.sqlite import TestTask

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        self.running = False
        self.check_interval = 60  # 每60秒检查一次
    
    async def start(self):
        """启动调度器"""
        self.running = True
        logger.info("Task scheduler started")
        
        while self.running:
            try:
                await self.check_pending_tasks()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("Task scheduler stopped")
    
    async def check_pending_tasks(self):
        """检查待执行的定时任务"""
        async for db in get_db():
            try:
                # 查找所有待执行的定时任务
                now = datetime.utcnow()
                
                # 查询已到期的定时任务
                query = select(TestTask).where(
                    and_(
                        TestTask.task_status == "pending",
                        TestTask.schedule_type.in_(["scheduled", "recurring"]),
                        TestTask.scheduled_at <= now
                    )
                )
                
                result = await db.execute(query)
                tasks = result.scalars().all()
                
                for task in tasks:
                    await self.trigger_task(task, db)
                
                # 处理循环任务
                await self.process_recurring_tasks(db)
                
            except Exception as e:
                logger.error(f"Error checking pending tasks: {e}")
            finally:
                await db.close()
    
    async def trigger_task(self, task: TestTask, db: AsyncSession):
        """触发任务执行"""
        try:
            # 更新任务状态
            task.task_status = "running"
            task.started_at = datetime.utcnow()
            await db.commit()
            
            logger.info(f"Triggered scheduled task: {task.task_name} (ID: {task.id})")
            
            # TODO: 发送任务到执行队列或通知Agent执行
            
        except Exception as e:
            logger.error(f"Error triggering task: {e}")
    
    async def process_recurring_tasks(self, db: AsyncSession):
        """处理循环任务"""
        try:
            now = datetime.utcnow()
            
            # 查询需要执行的循环任务
            query = select(TestTask).where(
                and_(
                    TestTask.task_status == "completed",
                    TestTask.schedule_type == "recurring",
                    TestTask.cron_expression.isnot(None)
                )
            )
            
            result = await db.execute(query)
            tasks = result.scalars().all()
            
            for task in tasks:
                next_run = self.calculate_next_run(task.cron_expression, task.completed_at)
                
                if next_run and next_run <= now:
                    # 创建新的任务实例
                    new_task = TestTask(
                        task_name=task.task_name,
                        task_type=task.task_type,
                        task_status="pending",
                        target_device_ids=task.target_device_ids,
                        target_departments=task.target_departments,
                        target_positions=task.target_positions,
                        test_script_id=task.test_script_id,
                        test_duration_seconds=task.test_duration_seconds,
                        sample_interval_ms=task.sample_interval_ms,
                        schedule_type=task.schedule_type,
                        scheduled_at=next_run,
                        cron_expression=task.cron_expression
                    )
                    db.add(new_task)
                    await db.commit()
                    
                    logger.info(f"Created recurring task instance: {task.task_name}")
        
        except Exception as e:
            logger.error(f"Error processing recurring tasks: {e}")
    
    def calculate_next_run(self, cron_expression: Optional[str], last_run: datetime) -> Optional[datetime]:
        """根据cron表达式计算下次执行时间"""
        if not cron_expression:
            return None
        
        # 简单的cron解析（支持基本格式）
        # 格式: "interval:60" 表示每60分钟执行一次
        # 格式: "daily:HH:MM" 表示每天固定时间执行
        # 格式: "weekly:0:HH:MM" 表示每周固定时间执行
        
        try:
            if cron_expression.startswith("interval:"):
                # 间隔任务
                minutes = int(cron_expression.split(":")[1])
                return last_run + timedelta(minutes=minutes)
            
            elif cron_expression.startswith("daily:"):
                # 每日任务
                time_str = cron_expression.split(":")[1]
                hour, minute = map(int, time_str.split(":"))
                next_run = last_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= last_run:
                    next_run += timedelta(days=1)
                return next_run
            
            elif cron_expression.startswith("weekly:"):
                # 每周任务
                parts = cron_expression.split(":")
                day_of_week = int(parts[1])
                time_str = parts[2]
                hour, minute = map(int, time_str.split(":"))
                next_run = last_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # 调整到目标星期
                days_ahead = day_of_week - next_run.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_run += timedelta(days=days_ahead)
                
                return next_run
        
        except Exception as e:
            logger.error(f"Error parsing cron expression: {e}")
        
        return None


# 全局调度器实例
scheduler = TaskScheduler()


async def start_scheduler():
    """启动调度器"""
    await scheduler.start()


def stop_scheduler():
    """停止调度器"""
    scheduler.stop()

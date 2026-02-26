"""
Celery configuration and tasks for Hardware Benchmark System
"""
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import asyncio

# Celery configuration
celery_app = Celery(
    'hardware_benchmark',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'check-device-status': {
            'task': 'app.tasks.scheduler.check_device_status',
            'schedule': 60.0,  # Every minute
        },
        'process-scheduled-tasks': {
            'task': 'app.tasks.scheduler.process_scheduled_tasks',
            'schedule': 30.0,  # Every 30 seconds
        },
    }
)


@celery_app.task(name='app.tasks.test.execute_benchmark')
def execute_benchmark_task(task_id: str, device_id: str, test_config: dict):
    """Execute benchmark test on device"""
    import httpx
    
    async def run_benchmark():
        # This would connect to the agent and run benchmark
        # For now, simulate the benchmark execution
        try:
            # Call agent API to start benchmark
            async with httpx.AsyncClient() as client:
                # Simulate benchmark duration
                await asyncio.sleep(5)
                
                # Return mock results
                return {
                    "task_id": task_id,
                    "device_id": device_id,
                    "test_status": "completed",
                    "overall_score": 85.5,
                    "cpu_score": 82.0,
                    "gpu_score": 88.0,
                    "memory_score": 80.0,
                    "disk_score": 90.0,
                    "duration_seconds": 300
                }
        except Exception as e:
            return {
                "task_id": task_id,
                "device_id": device_id,
                "test_status": "failed",
                "error": str(e)
            }
    
    return asyncio.run(run_benchmark())


@celery_app.task(name='app.tasks.scheduler.check_device_status')
def check_device_status():
    """Check device status and update offline devices"""
    from app.core.database import get_db_session
    from app.models.database import Device
    
    async def update_status():
        async with get_db_session() as session:
            from sqlalchemy import select, and_
            from datetime import datetime, timedelta
            
            # Find devices not seen in last 5 minutes
            cutoff = datetime.utcnow() - timedelta(minutes=5)
            result = await session.execute(
                select(Device).where(
                    and_(
                        Device.status == 'online',
                        Device.last_seen_at < cutoff
                    )
                )
            )
            offline_devices = result.scalars().all()
            
            for device in offline_devices:
                device.status = 'offline'
                print(f"Device {device.device_name} marked as offline")
            
            await session.commit()
    
    asyncio.run(update_status())


@celery_app.task(name='app.tasks.scheduler.process_scheduled_tasks')
def process_scheduled_tasks():
    """Process tasks that are scheduled for execution"""
    from app.core.database import get_db_session
    from app.models.database import TestTask
    
    async def process():
        async with get_db_session() as session:
            from sqlalchemy import select, and_
            from datetime import datetime
            
            # Find pending scheduled tasks
            result = await session.execute(
                select(TestTask).where(
                    and_(
                        TestTask.task_status == 'pending',
                        TestTask.schedule_type == 'scheduled',
                        TestTask.scheduled_at <= datetime.utcnow()
                    )
                )
            )
            tasks = result.scalars().all()
            
            for task in tasks:
                task.task_status = 'running'
                task.started_at = datetime.utcnow()
                print(f"Starting scheduled task: {task.task_name}")
            
            await session.commit()
    
    asyncio.run(process())


@celery_app.task(name='app.tasks.analysis.analyze_results')
def analyze_test_results(result_id: str):
    """Analyze test results and generate insights"""
    from app.core.database import get_db_session
    from app.models.database import TestResult, PositionStandard, Device
    
    async def analyze():
        async with get_db_session() as session:
            from sqlalchemy import select
            
            # Get result with device and standard
            result = await session.execute(
                select(TestResult).where(TestResult.id == result_id)
            )
            test_result = result.scalar_one_or_none()
            
            if not test_result:
                return {"error": "Result not found"}
            
            # Get device
            device = await session.execute(
                select(Device).where(Device.id == test_result.device_id)
            )
            device = device.scalar_one_or_none()
            
            # Basic analysis
            scores = {
                "cpu": test_result.cpu_score or 0,
                "gpu": test_result.gpu_score or 0,
                "memory": test_result.memory_score or 0,
                "disk": test_result.disk_score or 0
            }
            
            # Find bottleneck
            bottleneck = min(scores, key=scores.get)
            test_result.bottleneck_type = bottleneck.upper()
            
            # Generate upgrade suggestions
            suggestions = []
            if scores["cpu"] < 70:
                suggestions.append({
                    "component": "CPU",
                    "current": device.cpu_model if device else "Unknown",
                    "recommendation": "Consider upgrading to a higher core count CPU"
                })
            if scores["gpu"] < 70:
                suggestions.append({
                    "component": "GPU",
                    "current": device.gpu_model if device else "Unknown",
                    "recommendation": "Consider upgrading to a GPU with more VRAM"
                })
            if scores["memory"] < 70:
                suggestions.append({
                    "component": "Memory",
                    "current": f"{device.ram_total_gb}GB" if device and device.ram_total_gb else "Unknown",
                    "recommendation": "Consider adding more RAM"
                })
            
            test_result.upgrade_suggestion = suggestions
            
            # Determine if standard is met
            if test_result.standard_id:
                standard = await session.execute(
                    select(PositionStandard).where(PositionStandard.id == test_result.standard_id)
                )
                standard = standard.scalar_one_or_none()
                
                if standard:
                    is_met = True
                    fail_reasons = []
                    
                    if device:
                        if standard.cpu_min_cores and device.cpu_cores < standard.cpu_min_cores:
                            is_met = False
                            fail_reasons.append(f"CPU cores ({device.cpu_cores}) below minimum ({standard.cpu_min_cores})")
                        if standard.ram_min_gb and device.ram_total_gb < standard.ram_min_gb:
                            is_met = False
                            fail_reasons.append(f"RAM ({device.ram_total_gb}GB) below minimum ({standard.ram_min_gb}GB)")
                    
                    test_result.is_standard_met = is_met
                    test_result.fail_reasons = fail_reasons
            
            await session.commit()
            return {"result_id": result_id, "analyzed": True}
    
    return asyncio.run(analyze())

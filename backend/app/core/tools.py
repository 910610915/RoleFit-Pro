import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.sqlite import Device, TestTask, TestResult, TestSoftware, JobScript
from app.schemas.device import DeviceResponse
from app.schemas.task import TaskResponse
from app.schemas.result import ResultResponse

def get_devices(db: Session, status: Optional[str] = None, gpu_model: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    查询设备列表，支持按状态、显卡型号筛选
    
    Args:
        status: 设备状态 (online/offline/busy/idle)
        gpu_model: 显卡型号关键词 (如 "4090", "3080")
        limit: 返回数量限制
    """
    query = select(Device)
    
    if status:
        query = query.where(Device.status == status)
        
    if gpu_model:
        query = query.where(Device.gpu_model.ilike(f"%{gpu_model}%"))
        
    query = query.limit(limit)
    devices = db.execute(query).scalars().all()
    
    return [
        {
            "id": d.id,
            "name": d.device_name,
            "status": d.status,
            "cpu": d.cpu_model,
            "gpu": d.gpu_model,
            "ram": f"{d.ram_total_gb}GB",
            "last_seen": d.last_seen_at.isoformat() if d.last_seen_at else None
        }
        for d in devices
    ]

def get_tasks(db: Session, status: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    查询最近的测试任务
    
    Args:
        status: 任务状态 (pending/running/completed/failed)
        limit: 返回数量限制
    """
    query = select(TestTask).order_by(desc(TestTask.created_at))
    
    if status:
        query = query.where(TestTask.task_status == status)
        
    query = query.limit(limit)
    tasks = db.execute(query).scalars().all()
    
    return [
        {
            "id": t.id,
            "name": t.task_name,
            "type": t.task_type,
            "status": t.task_status,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tasks
    ]

def get_results(db: Session, device_name: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    查询最近的测试结果
    
    Args:
        device_name: 设备名称关键词
        limit: 返回数量限制
    """
    query = select(TestResult).join(Device).order_by(desc(TestResult.created_at))
    
    if device_name:
        query = query.where(Device.device_name.ilike(f"%{device_name}%"))
        
    query = query.limit(limit)
    results = db.execute(query).scalars().all()
    
    return [
        {
            "id": r.id,
            "device": r.device.device_name if r.device else "Unknown",
            "test_type": r.test_type,
            "status": r.test_status,
            "score": r.overall_score,
            "duration": f"{r.duration_seconds}s",
            "date": r.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for r in results
    ]

def list_software(db: Session, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    查询支持的测试软件列表
    
    Args:
        category: 软件类别 (DEV/ART/VFX/VIDEO)
    """
    query = select(TestSoftware).where(TestSoftware.is_active == True)
    
    if category:
        query = query.where(TestSoftware.category == category)
        
    software = db.execute(query).scalars().all()
    
    return [
        {
            "name": s.software_name,
            "code": s.software_code,
            "category": s.category,
            "version": s.version
        }
        for s in software
    ]

# Tool Definitions (Schema for LLM)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_devices",
            "description": "查询设备列表，可以查看在线状态、硬件配置（CPU/GPU/内存）等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["online", "offline", "busy", "idle"],
                        "description": "设备状态筛选"
                    },
                    "gpu_model": {
                        "type": "string",
                        "description": "显卡型号关键词，如 '4090', '3080'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认10"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "查询测试任务列表，查看正在运行或已完成的任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "running", "completed", "failed"],
                        "description": "任务状态筛选"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认5"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_results",
            "description": "查询测试结果，查看跑分数据、测试是否通过等",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "设备名称关键词"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量限制，默认5"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_software",
            "description": "查询支持的测试软件列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["DEV", "ART", "VFX", "VIDEO"],
                        "description": "软件类别筛选"
                    }
                },
                "required": []
            }
        }
    }
]

# Map function names to actual functions
AVAILABLE_TOOLS = {
    "get_devices": get_devices,
    "get_tasks": get_tasks,
    "get_results": get_results,
    "list_software": list_software
}

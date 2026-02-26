from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Device Schemas
class DeviceBase(BaseModel):
    device_name: str
    mac_address: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class DeviceHardwareInfo(BaseModel):
    """Hardware information from agent"""
    cpu_model: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_base_clock: Optional[float] = None
    
    gpu_model: Optional[str] = None
    gpu_vram_mb: Optional[int] = None
    gpu_driver_version: Optional[str] = None
    all_gpus: Optional[list] = None  # JSON: 所有显卡
    
    ram_total_gb: Optional[float] = None
    ram_frequency: Optional[int] = None
    ram_sticks: Optional[int] = None
    all_memory: Optional[list] = None  # JSON: 所有内存条
    
    disk_model: Optional[str] = None
    disk_capacity_tb: Optional[float] = None
    disk_type: Optional[str] = None
    all_disks: Optional[list] = None  # JSON: 所有磁盘
    
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    os_build: Optional[str] = None


class DeviceResponse(DeviceBase, DeviceHardwareInfo):
    id: str
    status: str
    last_seen_at: Optional[datetime]
    registered_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[DeviceResponse]


# Agent Schemas
class AgentRegisterRequest(BaseModel):
    device_name: str
    hostname: Optional[str] = None
    mac_address: str
    ip_address: str
    agent_version: str = "1.0.0"
    os_info: Optional[dict] = None
    # Hardware info fields
    cpu_model: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    cpu_base_clock: Optional[float] = None
    gpu_model: Optional[str] = None
    gpu_vram_mb: Optional[int] = None
    gpu_driver_version: Optional[str] = None
    all_gpus: Optional[list] = None
    ram_total_gb: Optional[float] = None
    ram_frequency: Optional[int] = None
    ram_sticks: Optional[int] = None
    all_memory: Optional[list] = None
    disk_model: Optional[str] = None
    disk_capacity_tb: Optional[float] = None
    disk_type: Optional[str] = None
    all_disks: Optional[list] = None


class AgentHeartbeatRequest(BaseModel):
    mac_address: str
    status: str
    current_task_id: Optional[str] = None
    system_info: Optional[dict] = None

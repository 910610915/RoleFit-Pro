from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Any
from datetime import datetime, timedelta
import uuid
import json

from app.core.database import get_db_sync
from app.models.sqlite import Device, User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    AgentRegisterRequest,
    AgentHeartbeatRequest,
    DeviceHardwareInfo,
)

router = APIRouter(prefix="/devices", tags=["Devices"])


def device_to_response(device: Device) -> dict:
    """Convert Device model to response dict, parsing JSON fields"""
    result = {}
    for column in device.__table__.columns:
        value = getattr(device, column.name)
        if column.name in ["all_gpus", "all_memory", "all_disks"] and value:
            try:
                result[column.name] = json.loads(value)
            except:
                result[column.name] = value
        else:
            result[column.name] = value
    return result


# Agent endpoints (no auth required)
@router.post(
    "/agent/register",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    register_data: AgentRegisterRequest, db: Session = Depends(get_db_sync)
):
    """Register a new device from agent"""
    # Check if device already exists
    result = db.execute(
        select(Device).where(Device.mac_address == register_data.mac_address)
    )
    existing_device = result.scalar_one_or_none()

    # Get data as dict, excluding unset values
    data = register_data.model_dump(exclude_none=True)

    # Handle JSON fields - convert to string for SQLite
    for json_field in ["all_gpus", "all_memory", "all_disks"]:
        if json_field in data and data[json_field]:
            if isinstance(data[json_field], (list, dict)):
                data[json_field] = json.dumps(data[json_field])

    if existing_device:
        # Update existing device
        for key, value in data.items():
            if hasattr(existing_device, key):
                setattr(existing_device, key, value)
        existing_device.last_seen_at = datetime.utcnow()
        existing_device.status = "online"
        db.commit()
        db.refresh(existing_device)
        return device_to_response(existing_device)

    # Create new device with basic fields
    device_data = {
        "device_name": register_data.device_name,
        "mac_address": register_data.mac_address,
        "ip_address": register_data.ip_address or "",
        "hostname": register_data.hostname or "",
        "status": "online",
        "last_seen_at": datetime.utcnow(),
    }

    # Add hardware fields if present
    for key in data:
        if key not in [
            "device_name",
            "mac_address",
            "ip_address",
            "hostname",
            "agent_version",
            "os_info",
        ]:
            device_data[key] = data[key]

    db_device = Device(**device_data)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    return device_to_response(db_device)


@router.post("/agent/heartbeat", status_code=status.HTTP_200_OK)
def device_heartbeat(
    heartbeat_data: AgentHeartbeatRequest, db: Session = Depends(get_db_sync)
):
    """Device heartbeat endpoint"""
    result = db.execute(
        select(Device).where(Device.mac_address == heartbeat_data.mac_address)
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update device status
    device.status = heartbeat_data.status
    device.last_seen_at = datetime.utcnow()

    # Update hardware info if provided in system_info
    if heartbeat_data.system_info:
        sys_info = heartbeat_data.system_info
        # CPU info
        if "cpu_model" in sys_info:
            device.cpu_model = sys_info.get("cpu_model")
        if "cpu_cores" in sys_info:
            device.cpu_cores = sys_info.get("cpu_cores")
        if "cpu_threads" in sys_info:
            device.cpu_threads = sys_info.get("cpu_threads")
        # GPU info
        if "gpu_model" in sys_info:
            device.gpu_model = sys_info.get("gpu_model")
        if "gpu_vram_mb" in sys_info:
            device.gpu_vram_mb = sys_info.get("gpu_vram_mb")
        # RAM info
        if "ram_total_gb" in sys_info:
            device.ram_total_gb = sys_info.get("ram_total_gb")
        # Disk info
        if "disk_model" in sys_info:
            device.disk_model = sys_info.get("disk_model")
        if "disk_type" in sys_info:
            device.disk_type = sys_info.get("disk_type")

    db.commit()

    return {"status": "ok"}


# User endpoints (auth required)
@router.get("", response_model=DeviceListResponse)
def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    department: Optional[str] = None,
    position: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    """Get device list"""
    query = select(Device)

    # Apply filters
    if status:
        query = query.where(Device.status == status)
    if department:
        query = query.where(Device.department == department)
    if position:
        query = query.where(Device.position == position)
    if keyword:
        query = query.where(
            or_(
                Device.device_name.ilike(f"%{keyword}%"),
                Device.mac_address.ilike(f"%{keyword}%"),
            )
        )

    # Count total
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(count_query) or 0

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = db.execute(query)
    devices = result.scalars().all()

    return DeviceListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DeviceResponse.model_validate(device_to_response(d)) for d in devices],
    )


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db_sync)):
    """Get device details"""
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    return device_to_response(device)


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    device_id: str, device_data: DeviceUpdate, db: Session = Depends(get_db_sync)
):
    """Update device information"""
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    # Update fields
    for key, value in device_data.model_dump(exclude_unset=True).items():
        setattr(device, key, value)

    db.commit()
    db.refresh(device)

    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: str, db: Session = Depends(get_db_sync)):
    """Delete device"""
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
        )

    db.delete(device)
    db.commit()

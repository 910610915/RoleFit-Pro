from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Any
from datetime import datetime, timedelta
import uuid
import json
import logging

logger = logging.getLogger(__name__)

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

    # If device not found, auto-register it
    if not device:
        logger.info(f"Device not found, auto-registering: {heartbeat_data.mac_address}")
        device = Device(
            device_name=heartbeat_data.mac_address[:8],
            mac_address=heartbeat_data.mac_address,
            ip_address="",
            hostname="",
            status=heartbeat_data.status,
            last_seen_at=datetime.utcnow(),
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return {"status": "registered", "device_id": str(device.id)}

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
                Device.ip_address.ilike(f"%{keyword}%"),
                Device.hostname.ilike(f"%{keyword}%"),
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


# ==================== Device Profile (设备画像) ====================


@router.get("/{device_id}/profile")
def get_device_profile(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备画像 - 完整的设备档案"""
    from sqlalchemy import select, func
    from app.models.sqlite import TestResult, PerformanceMetric

    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # Get test results count and latest score
    test_result = db.execute(
        select(
            func.count(TestResult.id).label("total_tests"),
            func.avg(TestResult.overall_score).label("avg_score"),
            func.max(TestResult.created_at).label("last_test"),
        ).where(TestResult.device_id == device_id)
    )
    test_stats = test_result.fetchone()

    # Get performance metrics count
    metrics_result = db.execute(
        select(func.count(PerformanceMetric.id)).where(
            PerformanceMetric.device_id == device_id
        )
    )
    metrics_count = metrics_result.scalar() or 0

    # Build comprehensive profile
    profile = {
        # 基础信息
        "basic_info": {
            "id": device.id,
            "device_name": device.device_name,
            "hostname": device.hostname,
            "mac_address": device.mac_address,
            "ip_address": device.ip_address,
            "status": device.status,
            "registered_at": device.registered_at.isoformat()
            if device.registered_at
            else None,
            "last_seen_at": device.last_seen_at.isoformat()
            if device.last_seen_at
            else None,
        },
        # 硬件信息
        "hardware": {
            "cpu": {
                "model": device.cpu_model,
                "cores": device.cpu_cores,
                "threads": device.cpu_threads,
                "base_clock": device.cpu_base_clock,
            },
            "gpu": {
                "model": device.gpu_model,
                "vram_mb": device.gpu_vram_mb,
                "driver_version": device.gpu_driver_version,
            },
            "memory": {
                "total_gb": device.ram_total_gb,
                "frequency": device.ram_frequency,
            },
            "storage": {
                "model": device.disk_model,
                "capacity_tb": device.disk_capacity_tb,
                "type": device.disk_type,
            },
            "os": {
                "name": device.os_name,
                "version": device.os_version,
                "build": device.os_build,
            },
        },
        # 归属信息
        "ownership": {
            "department": device.department,
            "position": device.position,
            "assigned_to": device.assigned_to,
            "employee_name": device.employee_name,
            "employee_id": device.employee_id,
            "employee_email": device.employee_email,
        },
        # 采购信息
        "purchase": {
            "purchase_date": device.purchase_date.isoformat()
            if device.purchase_date
            else None,
            "purchase_price": device.purchase_price,
            "purchase_vendor": device.purchase_vendor,
            "warranty_expire_date": device.warranty_expire_date.isoformat()
            if device.warranty_expire_date
            else None,
            "invoice_number": device.invoice_number,
        },
        # 资产信息
        "asset": {
            "asset_tag": device.asset_tag,
            "serial_number": device.serial_number,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "location": device.location,
        },
        # 使用统计
        "usage_stats": {
            "total_test_count": test_stats[0] or 0,
            "average_score": float(test_stats[1]) if test_stats[1] else None,
            "last_test_date": test_stats[2].isoformat() if test_stats[2] else None,
            "metrics_count": metrics_count,
            "total_uptime_hours": device.total_uptime_hours,
        },
        # 备注
        "notes": device.notes,
    }

    return profile


@router.put("/{device_id}/profile")
def update_device_profile(
    device_id: str, profile_data: dict, db: Session = Depends(get_db_sync)
):
    """更新设备画像"""
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # Update ownership fields
    if "employee_name" in profile_data:
        device.employee_name = profile_data["employee_name"]
    if "employee_id" in profile_data:
        device.employee_id = profile_data["employee_id"]
    if "employee_email" in profile_data:
        device.employee_email = profile_data["employee_email"]
    if "department" in profile_data:
        device.department = profile_data["department"]
    if "position" in profile_data:
        device.position = profile_data["position"]
    if "assigned_to" in profile_data:
        device.assigned_to = profile_data["assigned_to"]

    # Update purchase fields
    if "purchase_date" in profile_data:
        device.purchase_date = profile_data["purchase_date"]
    if "purchase_price" in profile_data:
        device.purchase_price = profile_data["purchase_price"]
    if "purchase_vendor" in profile_data:
        device.purchase_vendor = profile_data["purchase_vendor"]
    if "warranty_expire_date" in profile_data:
        device.warranty_expire_date = profile_data["warranty_expire_date"]
    if "invoice_number" in profile_data:
        device.invoice_number = profile_data["invoice_number"]

    # Update asset fields
    if "asset_tag" in profile_data:
        device.asset_tag = profile_data["asset_tag"]
    if "serial_number" in profile_data:
        device.serial_number = profile_data["serial_number"]
    if "manufacturer" in profile_data:
        device.manufacturer = profile_data["manufacturer"]
    if "model" in profile_data:
        device.model = profile_data["model"]
    if "location" in profile_data:
        device.location = profile_data["location"]

    # Update notes
    if "notes" in profile_data:
        device.notes = profile_data["notes"]

    db.commit()

    return {"message": "设备画像已更新", "device_id": device_id}

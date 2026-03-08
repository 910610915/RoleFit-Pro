"""
远程控制 API
提供设备的远程控制功能：关机、重启、锁定、唤醒、命令执行
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from app.core.database import get_db_sync
from app.models.sqlite import Device, ControlCommand

router = APIRouter(prefix="/control", tags=["Remote Control"])


# Request/Response Models
class ControlCommandRequest(BaseModel):
    """控制命令请求"""

    command_type: str  # shutdown, restart, lock, unlock, wake, execute
    target_software: Optional[str] = None
    command_params: Optional[Dict[str, Any]] = None
    priority: int = 5


class ControlCommandResponse(BaseModel):
    """控制命令响应"""

    id: str
    device_id: str
    command_type: str
    status: str
    priority: int
    created_at: datetime
    sent_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None


class WakeOnLANRequest(BaseModel):
    """Wake-on-LAN 请求"""

    mac_address: str
    broadcast_ip: str = "255.255.255.255"
    port: int = 9


# Command type definitions
COMMAND_TYPES = {
    "shutdown": "关机",
    "restart": "重启",
    "lock": "锁定",
    "unlock": "解锁",
    "wake": "唤醒",
    "execute": "执行命令",
    "cancel": "取消命令",
}

VALID_COMMAND_TYPES = list(COMMAND_TYPES.keys())


@router.post("/devices/{device_id}/command", response_model=ControlCommandResponse)
def send_command(
    device_id: str, request: ControlCommandRequest, db: Session = Depends(get_db_sync)
):
    """向设备发送控制命令"""
    # Validate command type
    if request.command_type not in VALID_COMMAND_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的命令类型: {request.command_type}。有效类型: {VALID_COMMAND_TYPES}",
        )

    # Check device exists
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # Check device is online
    if device.status != "online":
        raise HTTPException(
            status_code=400, detail=f"设备离线，无法发送命令。当前状态: {device.status}"
        )

    # Create command
    command = ControlCommand(
        id=str(uuid.uuid4()),
        device_id=device_id,
        command_type=request.command_type,
        target_software=request.target_software,
        command_params=json.dumps(request.command_params)
        if request.command_params
        else None,
        status="pending",
        priority=request.priority,
        source="manual",
        triggered_by="user",
    )

    db.add(command)
    db.commit()
    db.refresh(command)

    return {
        "id": command.id,
        "device_id": command.device_id,
        "command_type": command.command_type,
        "status": command.status,
        "priority": command.priority,
        "created_at": command.created_at,
        "sent_at": command.sent_at,
        "acknowledged_at": command.acknowledged_at,
        "completed_at": command.completed_at,
        "result": command.result,
        "error_message": command.error_message,
    }


@router.get(
    "/devices/{device_id}/commands", response_model=List[ControlCommandResponse]
)
def get_device_commands(
    device_id: str, limit: int = 20, db: Session = Depends(get_db_sync)
):
    """获取设备的控制命令历史"""
    # Check device exists
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # Get commands
    result = db.execute(
        select(ControlCommand)
        .where(ControlCommand.device_id == device_id)
        .order_by(ControlCommand.created_at.desc())
        .limit(limit)
    )
    commands = result.scalars().all()

    return [
        {
            "id": cmd.id,
            "device_id": cmd.device_id,
            "command_type": cmd.command_type,
            "status": cmd.status,
            "priority": cmd.priority,
            "created_at": cmd.created_at,
            "sent_at": cmd.sent_at,
            "acknowledged_at": cmd.acknowledged_at,
            "completed_at": cmd.completed_at,
            "result": cmd.result,
            "error_message": cmd.error_message,
        }
        for cmd in commands
    ]


@router.get("/commands/{command_id}", response_model=ControlCommandResponse)
def get_command(command_id: str, db: Session = Depends(get_db_sync)):
    """获取命令详情"""
    result = db.execute(select(ControlCommand).where(ControlCommand.id == command_id))
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="命令不存在")

    return {
        "id": command.id,
        "device_id": command.device_id,
        "command_type": command.command_type,
        "status": command.status,
        "priority": command.priority,
        "created_at": command.created_at,
        "sent_at": command.sent_at,
        "acknowledged_at": command.acknowledged_at,
        "completed_at": command.completed_at,
        "result": command.result,
        "error_message": command.error_message,
    }


@router.delete("/commands/{command_id}")
def cancel_command(command_id: str, db: Session = Depends(get_db_sync)):
    """取消命令"""
    result = db.execute(select(ControlCommand).where(ControlCommand.id == command_id))
    command = result.scalar_one_or_none()

    if not command:
        raise HTTPException(status_code=404, detail="命令不存在")

    if command.status not in ["pending", "sent"]:
        raise HTTPException(
            status_code=400, detail=f"无法取消状态为 '{command.status}' 的命令"
        )

    command.status = "cancelled"
    db.commit()

    return {"message": "命令已取消", "command_id": command_id}


@router.post("/wake-on-lan")
def wake_on_lan(request: WakeOnLANRequest):
    """发送 Wake-on-LAN 包唤醒设备"""
    import socket

    try:
        # Parse MAC address
        mac = request.mac_address.replace(":", "-").replace(".", "-")
        mac_bytes = bytes.fromhex(mac.replace("-", ""))

        # Create Magic Packet (broadcast address + 16 * MAC address)
        magic_packet = b"\xff" * 6 + mac_bytes * 16

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Send packet
        sock.sendto(magic_packet, (request.broadcast_ip, request.port))
        sock.close()

        return {
            "success": True,
            "message": f"Wake-on-LAN 包已发送到 {request.mac_address}",
            "mac_address": request.mac_address,
            "broadcast_ip": request.broadcast_ip,
            "port": request.port,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Wake-on-LAN 失败: {str(e)}")


@router.get("/command-types")
def get_command_types():
    """获取支持的命令类型列表"""
    return {
        "command_types": [
            {
                "type": cmd_type,
                "name": cmd_name,
                "description": get_command_description(cmd_type),
            }
            for cmd_type, cmd_name in COMMAND_TYPES.items()
        ]
    }


def get_command_description(command_type: str) -> str:
    """获取命令描述"""
    descriptions = {
        "shutdown": "关闭设备电源",
        "restart": "重启设备",
        "lock": "锁定设备（锁定键盘鼠标）",
        "unlock": "解锁设备",
        "wake": "唤醒设备（Wake-on-LAN）",
        "execute": "执行自定义命令",
        "cancel": "取消待执行的命令",
    }
    return descriptions.get(command_type, "")


@router.get("/devices/{device_id}/quick-actions")
def get_quick_actions(device_id: str, db: Session = Depends(get_db_sync)):
    """获取设备的快速操作列表"""
    # Check device exists
    result = db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    is_online = device.status == "online"

    return {
        "device_id": device_id,
        "is_online": is_online,
        "quick_actions": [
            {
                "type": "shutdown",
                "name": "关机",
                "icon": "power",
                "disabled": not is_online,
                "confirm": "确定要关闭该设备吗？",
            },
            {
                "type": "restart",
                "name": "重启",
                "icon": "refresh",
                "disabled": not is_online,
                "confirm": "确定要重启该设备吗？",
            },
            {
                "type": "lock",
                "name": "锁定",
                "icon": "lock",
                "disabled": not is_online,
                "confirm": "确定要锁定该设备吗？",
            },
            {
                "type": "wake",
                "name": "唤醒",
                "icon": "wifi",
                "disabled": is_online,
                "confirm": None,
            },
        ],
    }

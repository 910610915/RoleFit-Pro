"""
第三方 API 集成服务
支持配置和对接外部系统：资产管理平台、企业通讯工具等
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
import requests
import logging

from app.core.database import get_db_sync
from app.models.sqlite import Device, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/third-party-apis", tags=["Third Party APIs"])


# ==================== Models ====================


class ThirdPartyAPI(BaseModel):
    """第三方 API 配置"""

    id: str
    name: str  # API 名称
    api_type: str  # asset_management, notification, webhook, etc.
    base_url: str  # API 基础 URL
    api_key: Optional[str] = None  # API Key
    secret: Optional[str] = None  # Secret
    enabled: bool = True
    headers: Optional[Dict[str, str]] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ThirdPartyAPICreate(BaseModel):
    """创建第三方 API 配置"""

    name: str
    api_type: str
    base_url: str
    api_key: Optional[str] = None
    secret: Optional[str] = None
    enabled: bool = True
    headers: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class ThirdPartyAPIUpdate(BaseModel):
    """更新第三方 API 配置"""

    name: Optional[str] = None
    api_type: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    secret: Optional[str] = None
    enabled: Optional[bool] = None
    headers: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class ThirdPartyAPIDBIn(BaseModel):
    """数据库中的第三方 API 配置"""

    id: str
    name: str
    api_type: str
    base_url: str
    api_key: Optional[str] = None
    secret: Optional[str] = None
    enabled: bool
    headers: Optional[str] = None  # JSON string in DB
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ==================== API Endpoints ====================


@router.get("", response_model=List[Dict[str, Any]])
def list_third_party_apis(
    enabled: Optional[bool] = None,
    api_type: Optional[str] = None,
    db: Session = Depends(get_db_sync),
):
    """获取第三方 API 列表"""
    query = "SELECT * FROM third_party_apis WHERE 1=1"
    params = {}

    if enabled is not None:
        query += " AND enabled = :enabled"
        params["enabled"] = enabled
    if api_type:
        query += " AND api_type = :api_type"
        params["api_type"] = api_type

    query += " ORDER BY created_at DESC"

    from sqlalchemy import text

    result = db.execute(text(query), params)
    rows = result.fetchall()

    apis = []
    for row in rows:
        apis.append(
            {
                "id": row[0],
                "name": row[1],
                "api_type": row[2],
                "base_url": row[3],
                "api_key": row[4] if row[4] else None,
                "secret": "***" if row[5] else None,  # Hide secret
                "enabled": bool(row[6]),
                "headers": json.loads(row[7]) if row[7] else None,
                "description": row[8],
                "created_at": row[9].isoformat() if row[9] else None,
                "updated_at": row[10].isoformat() if row[10] else None,
            }
        )

    return apis


@router.post("", response_model=Dict[str, Any])
def create_third_party_api(
    api_data: ThirdPartyAPICreate, db: Session = Depends(get_db_sync)
):
    """创建第三方 API 配置"""
    api_id = str(uuid.uuid4())
    now = datetime.utcnow()

    query = """
        INSERT INTO third_party_apis 
        (id, name, api_type, base_url, api_key, secret, enabled, headers, description, created_at, updated_at)
        VALUES (:id, :name, :api_type, :base_url, :api_key, :secret, :enabled, :headers, :description, :created_at, :updated_at)
    """

    from sqlalchemy import text

    db.execute(
        text(query),
        {
            "id": api_id,
            "name": api_data.name,
            "api_type": api_data.api_type,
            "base_url": api_data.base_url,
            "api_key": api_data.api_key,
            "secret": api_data.secret,
            "enabled": api_data.enabled,
            "headers": json.dumps(api_data.headers) if api_data.headers else None,
            "description": api_data.description,
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()

    return {"id": api_id, "message": "第三方 API 配置已创建"}


@router.get("/{api_id}", response_model=Dict[str, Any])
def get_third_party_api(api_id: str, db: Session = Depends(get_db_sync)):
    """获取第三方 API 详情"""
    from sqlalchemy import text

    result = db.execute(
        text("SELECT * FROM third_party_apis WHERE id = :id"), {"id": api_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="API 配置不存在")

    return {
        "id": row[0],
        "name": row[1],
        "api_type": row[2],
        "base_url": row[3],
        "api_key": row[4],
        "secret": row[5],
        "enabled": bool(row[6]),
        "headers": json.loads(row[7]) if row[7] else None,
        "description": row[8],
        "created_at": row[9].isoformat() if row[9] else None,
        "updated_at": row[10].isoformat() if row[10] else None,
    }


@router.put("/{api_id}", response_model=Dict[str, Any])
def update_third_party_api(
    api_id: str, api_data: ThirdPartyAPIUpdate, db: Session = Depends(get_db_sync)
):
    """更新第三方 API 配置"""
    from sqlalchemy import text

    # Check exists
    result = db.execute(
        text("SELECT id FROM third_party_apis WHERE id = :id"), {"id": api_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="API 配置不存在")

    # Build update query
    updates = []
    params = {"id": api_id, "updated_at": datetime.utcnow()}

    if api_data.name is not None:
        updates.append("name = :name")
        params["name"] = api_data.name
    if api_data.api_type is not None:
        updates.append("api_type = :api_type")
        params["api_type"] = api_data.api_type
    if api_data.base_url is not None:
        updates.append("base_url = :base_url")
        params["base_url"] = api_data.base_url
    if api_data.api_key is not None:
        updates.append("api_key = :api_key")
        params["api_key"] = api_data.api_key
    if api_data.secret is not None:
        updates.append("secret = :secret")
        params["secret"] = api_data.secret
    if api_data.enabled is not None:
        updates.append("enabled = :enabled")
        params["enabled"] = api_data.enabled
    if api_data.headers is not None:
        updates.append("headers = :headers")
        params["headers"] = json.dumps(api_data.headers)
    if api_data.description is not None:
        updates.append("description = :description")
        params["description"] = api_data.description

    if not updates:
        raise HTTPException(status_code=400, detail="没有要更新的字段")

    query = f"UPDATE third_party_apis SET {', '.join(updates)}, updated_at = :updated_at WHERE id = :id"
    db.execute(text(query), params)
    db.commit()

    return {"message": "第三方 API 配置已更新"}


@router.delete("/{api_id}")
def delete_third_party_api(api_id: str, db: Session = Depends(get_db_sync)):
    """删除第三方 API 配置"""
    from sqlalchemy import text

    result = db.execute(
        text("DELETE FROM third_party_apis WHERE id = :id"), {"id": api_id}
    )
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="API 配置不存在")

    return {"message": "第三方 API 配置已删除"}


@router.post("/{api_id}/test")
def test_third_party_api(api_id: str, db: Session = Depends(get_db_sync)):
    """测试第三方 API 连接"""
    from sqlalchemy import text

    result = db.execute(
        text("SELECT * FROM third_party_apis WHERE id = :id"), {"id": api_id}
    )
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="API 配置不存在")

    base_url = row[3]
    api_key = row[4]

    try:
        # Try a simple GET request
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        if row[7]:  # headers
            custom_headers = json.loads(row[7])
            headers.update(custom_headers)

        response = requests.get(
            f"{base_url}/health" if not base_url.endswith("/") else f"{base_url}health",
            headers=headers,
            timeout=10,
        )

        return {
            "success": True,
            "status_code": response.status_code,
            "message": "API 连接成功",
        }
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"API 连接失败: {str(e)}"}


@router.get("/types/list")
def get_api_types():
    """获取支持的 API 类型"""
    return {
        "api_types": [
            {
                "type": "asset_management",
                "name": "资产管理平台",
                "description": "对接企业资产管理系统，同步设备信息",
            },
            {
                "type": "notification",
                "name": "企业通讯工具",
                "description": "钉钉、企业微信、飞书等通知集成",
            },
            {"type": "webhook", "name": "Webhook", "description": "通用 Webhook 回调"},
            {
                "type": "sso",
                "name": "单点登录 (SSO)",
                "description": "企业 SSO 认证集成",
            },
            {
                "type": "monitoring",
                "name": "监控系统",
                "description": "对接企业监控系统",
            },
        ]
    }


# ==================== Integration Functions ====================


async def send_notification_to_webhook(webhook_url: str, data: Dict[str, Any]) -> bool:
    """发送通知到 Webhook"""
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Webhook notification failed: {e}")
        return False


async def sync_device_to_asset_system(
    device: Device, api_config: Dict[str, Any]
) -> bool:
    """同步设备到资产管理系统"""
    try:
        payload = {
            "device_name": device.device_name,
            "mac_address": device.mac_address,
            "ip_address": device.ip_address,
            "hostname": device.hostname,
            "cpu_model": device.cpu_model,
            "gpu_model": device.gpu_model,
            "ram_total_gb": device.ram_total_gb,
            "department": device.department,
            "assigned_to": device.assigned_to,
            "status": device.status,
        }

        headers = {"Authorization": f"Bearer {api_config.get('api_key')}"}
        response = requests.post(
            f"{api_config['base_url']}/devices",
            json=payload,
            headers=headers,
            timeout=30,
        )

        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Asset system sync failed: {e}")
        return False

"""
角色管理 API
提供角色的增删改查和权限配置功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json

from app.core.database import get_db_sync
from app.core.security import get_current_user, require_role
from app.models.sqlite import User

router = APIRouter(prefix="/roles", tags=["Roles & Permissions"])


# Role definitions
ROLE_DEFINITIONS = {
    "super_admin": {
        "name": "超级管理员",
        "description": "拥有系统所有权限",
        "permissions": ["*"],
        "level": 100,
    },
    "it_admin": {
        "name": "IT管理员",
        "description": "管理所有设备、用户、告警",
        "permissions": [
            "devices:read",
            "devices:write",
            "devices:delete",
            "users:read",
            "users:write",
            "alarms:read",
            "alarms:write",
            "tasks:read",
            "tasks:write",
            "performance:read",
            "control:execute",
            "audit:read",
        ],
        "level": 80,
    },
    "ops": {
        "name": "运维人员",
        "description": "监控系统、执行任务、远程控制",
        "permissions": [
            "devices:read",
            "alarms:read",
            "alarms:write",
            "tasks:read",
            "tasks:write",
            "performance:read",
            "control:execute",
        ],
        "level": 60,
    },
    "dept_admin": {
        "name": "部门管理员",
        "description": "管理本部门设备",
        "permissions": [
            "devices:read",
            "devices:write",
            "alarms:read",
            "tasks:read",
            "tasks:write",
            "performance:read",
        ],
        "level": 40,
    },
    "viewer": {
        "name": "只读用户",
        "description": "只读权限",
        "permissions": [
            "devices:read",
            "alarms:read",
            "tasks:read",
            "performance:read",
        ],
        "level": 10,
    },
}


# Request/Response Models
class RoleCreate(BaseModel):
    """创建角色请求"""

    role_code: str
    name: str
    description: Optional[str] = None
    permissions: List[str]
    department: Optional[str] = None


class RoleResponse(BaseModel):
    """角色响应"""

    role_code: str
    name: str
    description: Optional[str]
    permissions: List[str]
    department: Optional[str]
    level: int
    user_count: int = 0


class RoleUpdate(BaseModel):
    """更新角色请求"""

    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    department: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """更新用户角色请求"""

    role: str
    department: Optional[str] = None


@router.get("", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db_sync), current_user: dict = Depends(get_current_user)
):
    """获取角色列表"""
    # Count users per role
    role_user_counts = {}
    result = db.execute(select(User))
    users = result.scalars().all()
    for user in users:
        role_user_counts[user.role] = role_user_counts.get(user.role, 0) + 1

    roles = []
    for role_code, role_def in ROLE_DEFINITIONS.items():
        roles.append(
            RoleResponse(
                role_code=role_code,
                name=role_def["name"],
                description=role_def["description"],
                permissions=role_def["permissions"],
                department=None,
                level=role_def["level"],
                user_count=role_user_counts.get(role_code, 0),
            )
        )

    return sorted(roles, key=lambda x: x.level, reverse=True)


@router.get("/{role_code}", response_model=RoleResponse)
def get_role(
    role_code: str,
    db: Session = Depends(get_db_sync),
    current_user: dict = Depends(get_current_user),
):
    """获取角色详情"""
    if role_code not in ROLE_DEFINITIONS:
        raise HTTPException(status_code=404, detail="角色不存在")

    role_def = ROLE_DEFINITIONS[role_code]

    # Count users with this role
    result = db.execute(select(User).where(User.role == role_code))
    user_count = len(result.scalars().all())

    return RoleResponse(
        role_code=role_code,
        name=role_def["name"],
        description=role_def["description"],
        permissions=role_def["permissions"],
        department=None,
        level=role_def["level"],
        user_count=user_count,
    )


@router.get("/definitions/all")
def get_role_definitions():
    """获取所有预定义角色的权限定义"""
    return {
        "roles": ROLE_DEFINITIONS,
        "available_permissions": [
            "devices:read",
            "devices:write",
            "devices:delete",
            "users:read",
            "users:write",
            "users:delete",
            "alarms:read",
            "alarms:write",
            "tasks:read",
            "tasks:write",
            "tasks:delete",
            "performance:read",
            "control:execute",
            "audit:read",
            "audit:write",
            "settings:read",
            "settings:write",
            "roles:read",
            "roles:write",
        ],
    }


@router.post("/{role_code}/permissions/check")
def check_permission(
    role_code: str, permission: str, current_user: dict = Depends(get_current_user)
):
    """检查角色是否有特定权限"""
    if role_code not in ROLE_DEFINITIONS:
        raise HTTPException(status_code=404, detail="角色不存在")

    role_def = ROLE_DEFINITIONS[role_code]
    permissions = role_def["permissions"]

    # Admin has all permissions
    if "*" in permissions:
        has_permission = True
    else:
        has_permission = permission in permissions

    return {
        "role_code": role_code,
        "permission": permission,
        "has_permission": has_permission,
    }


# User role management endpoints
@router.get("/users", response_model=List[Dict[str, Any]])
def list_users_with_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    department: Optional[str] = None,
    db: Session = Depends(get_db_sync),
    current_user: dict = Depends(get_current_user),
):
    """获取用户列表及其角色"""
    query = select(User)

    if role:
        query = query.where(User.role == role)
    if department:
        query = query.where(User.department == department)

    from sqlalchemy import func

    count_query = select(func.count(User.id))
    if role:
        count_query = count_query.where(User.role == role)
    if department:
        count_query = count_query.where(User.department == department)

    total = db.execute(count_query).scalar() or 0

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
        for user in users
    ]


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    role_data: UserRoleUpdate,
    db: Session = Depends(get_db_sync),
    current_user: dict = Depends(require_role(["super_admin", "it_admin"])),
):
    """更新用户角色（仅管理员可操作）"""
    result = db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # Validate role
    if role_data.role not in ROLE_DEFINITIONS:
        raise HTTPException(status_code=400, detail="无效的角色")

    user.role = role_data.role
    if role_data.department is not None:
        user.department = role_data.department

    db.commit()

    return {
        "message": "用户角色已更新",
        "user_id": user_id,
        "new_role": user.role,
        "department": user.department,
    }


@router.get("/departments/list")
def list_departments(
    db: Session = Depends(get_db_sync), current_user: dict = Depends(get_current_user)
):
    """获取所有部门列表"""
    result = db.execute(select(User.department).distinct())
    departments = [row[0] for row in result.fetchall() if row[0]]
    return {"departments": sorted(departments)}


@router.get("/my-permissions")
def get_my_permissions(current_user: dict = Depends(get_current_user)):
    """获取当前用户的权限"""
    role = current_user.get("role", "viewer")

    if role not in ROLE_DEFINITIONS:
        return {"role": role, "permissions": [], "level": 0}

    role_def = ROLE_DEFINITIONS[role]
    return {
        "role": role,
        "role_name": role_def["name"],
        "permissions": role_def["permissions"],
        "level": role_def["level"],
        "department": current_user.get("department"),
    }

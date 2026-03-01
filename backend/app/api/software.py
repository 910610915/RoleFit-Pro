from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Optional, List
import os
import glob as glob_module

from app.core.database import get_db_sync
from app.core.config import settings
from app.models.sqlite import TestSoftware
from app.schemas.software import (
    SoftwareCreate, SoftwareUpdate, SoftwareResponse, 
    SoftwareListResponse, SoftwareForTask
)

router = APIRouter(prefix="/software", tags=["Software"])

# 获取软件存储目录
def get_software_storage_dir():
    """获取软件存储目录的绝对路径"""
    # 相对于 backend 目录
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    storage_dir = os.path.join(backend_dir, settings.software_storage_path)
    # 自动创建目录（如果不存在）
    os.makedirs(storage_dir, exist_ok=True)
    return storage_dir


@router.get("", response_model=SoftwareListResponse)
def list_software(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db_sync)
):
    """获取测试软件列表"""
    query = select(TestSoftware).where(TestSoftware.is_active == True)
    
    if category:
        query = query.where(TestSoftware.category == category)
    
    count_result = db.execute(select(func.count(TestSoftware.id)))
    total = count_result.scalar() or 0
    
    query = query.order_by(TestSoftware.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = db.execute(query)
    items = result.scalars().all()
    
    return SoftwareListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SoftwareResponse.model_validate(item) for item in items]
    )


@router.post("", response_model=SoftwareResponse, status_code=status.HTTP_201_CREATED)
def create_software(
    data: SoftwareCreate,
    db: Session = Depends(get_db_sync)
):
    """创建测试软件"""
    # 检查 software_code 是否已存在
    result = db.execute(
        select(TestSoftware).where(TestSoftware.software_code == data.software_code)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Software code already exists")
    
    software = TestSoftware(**data.model_dump())
    db.add(software)
    db.commit()
    db.refresh(software)
    return software


@router.get("/{software_id}", response_model=SoftwareResponse)
def get_software(
    software_id: str,
    db: Session = Depends(get_db_sync)
):
    """获取软件详情"""
    result = db.execute(select(TestSoftware).where(TestSoftware.id == software_id))
    software = result.scalar_one_or_none()
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    return software


@router.put("/{software_id}", response_model=SoftwareResponse)
def update_software(
    software_id: str,
    data: SoftwareUpdate,
    db: Session = Depends(get_db_sync)
):
    """更新软件"""
    result = db.execute(select(TestSoftware).where(TestSoftware.id == software_id))
    software = result.scalar_one_or_none()
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(software, key, value)
    
    db.commit()
    db.refresh(software)
    return software


@router.delete("/{software_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(
    software_id: str,
    db: Session = Depends(get_db_sync)
):
    """删除软件(软删除)"""
    result = db.execute(select(TestSoftware).where(TestSoftware.id == software_id))
    software = result.scalar_one_or_none()
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    
    software.is_active = False
    db.commit()
    return None


# ====== 软件分发相关 API ======

@router.get("/for-task/{software_id}", response_model=SoftwareForTask)
def get_software_for_task(
    software_id: str,
    db: Session = Depends(get_db_sync)
):
    """获取软件信息（用于任务下发到Agent）"""
    result = db.execute(select(TestSoftware).where(TestSoftware.id == software_id))
    software = result.scalar_one_or_none()
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    
    if not software.is_active:
        raise HTTPException(status_code=400, detail="Software is inactive")
    
    # 提取值（确保是Python原生类型）
    return SoftwareForTask(
        software_id=str(software.id),
        software_code=str(software.software_code),
        software_name=str(software.software_name),
        software_type=str(software.software_type) if software.software_type else 'portable',
        package_format=str(software.package_format) if software.package_format else None,
        storage_path=str(software.storage_path) if software.storage_path else None,
        target_install_path=str(software.target_install_path) if software.target_install_path else None,
        subfolder_name=str(software.subfolder_name) if software.subfolder_name else None,
        silent_install_cmd=str(software.silent_install_cmd) if software.silent_install_cmd else None,
        main_exe_relative_path=str(software.main_exe_relative_path) if software.main_exe_relative_path else None,
        detection_method=str(software.detection_method) if software.detection_method else 'file',
        detection_path=str(software.detection_path) if software.detection_path else None,
        detection_keyword=str(software.detection_keyword) if software.detection_keyword else None,
        version=str(software.version) if software.version else None
    )


@router.get("/download/{software_code}")
def download_software(
    software_code: str,
    db: Session = Depends(get_db_sync)
):
    """下载软件包"""
    # 查询软件信息
    result = db.execute(
        select(TestSoftware).where(
            TestSoftware.software_code == software_code,
            TestSoftware.is_active == True
        )
    )
    software = result.scalar_one_or_none()
    if not software:
        raise HTTPException(status_code=404, detail="Software not found")
    
    # 提取值
    storage_path_val = software.storage_path if software.storage_path else None
    package_format_val = software.package_format if software.package_format else None
    
    # 确定存储路径
    storage_dir = get_software_storage_dir()
    software_dir = os.path.join(storage_dir, software_code)
    
    if not os.path.exists(software_dir):
        raise HTTPException(status_code=404, detail="Software package not found on server")
    
    # 如果配置了 storage_path，使用它
    if storage_path_val:
        software_dir = os.path.join(software_dir, storage_path_val)
    
    if not os.path.exists(software_dir):
        raise HTTPException(status_code=404, detail="Software storage path not found")
    
    # 查找安装包文件
    format_ext = package_format_val.lower() if package_format_val else None
    allowed_extensions = []
    if format_ext:
        if format_ext == 'exe':
            allowed_extensions = ['.exe']
        elif format_ext == 'msi':
            allowed_extensions = ['.msi']
        elif format_ext == 'zip':
            allowed_extensions = ['.zip']
        elif format_ext == 'rar':
            allowed_extensions = ['.rar']
        elif format_ext == '7z':
            allowed_extensions = ['.7z']
    
    # 搜索文件
    files_found = []
    for ext in allowed_extensions:
        pattern = os.path.join(software_dir, f"*{ext}")
        files_found.extend(glob_module.glob(pattern))
    
    if not files_found:
        raise HTTPException(status_code=404, detail=f"No package files found for format: {format_ext}")
    
    # 返回第一个匹配的文件
    file_path = files_found[0]
    filename = os.path.basename(file_path)
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

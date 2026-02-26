from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SoftwareBase(BaseModel):
    software_name: str
    software_code: str
    vendor: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    launch_params: Optional[str] = None
    icon: Optional[str] = None  # 图标路径


class SoftwareCreate(SoftwareBase):
    # 安装配置
    software_type: Optional[str] = 'portable'  # installer / portable
    package_format: Optional[str] = None  # exe / msi / zip / rar / 7z
    storage_path: Optional[str] = None  # 服务器存储路径
    target_install_path: Optional[str] = None  # 目标机器安装目录
    subfolder_name: Optional[str] = None  # 安装后子文件夹
    silent_install_cmd: Optional[str] = None  # 静默安装命令
    main_exe_relative_path: Optional[str] = None  # 主程序相对路径
    
    # 检测配置
    detection_method: Optional[str] = 'file'  # process / registry / file
    detection_path: Optional[str] = None  # 检测路径
    detection_keyword: Optional[str] = None  # 检测关键字


class SoftwareUpdate(BaseModel):
    software_name: Optional[str] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    launch_params: Optional[str] = None
    icon: Optional[str] = None
    
    # 安装配置
    software_type: Optional[str] = None
    package_format: Optional[str] = None
    storage_path: Optional[str] = None
    target_install_path: Optional[str] = None
    subfolder_name: Optional[str] = None
    silent_install_cmd: Optional[str] = None
    main_exe_relative_path: Optional[str] = None
    
    # 检测配置
    detection_method: Optional[str] = None
    detection_path: Optional[str] = None
    detection_keyword: Optional[str] = None
    
    is_active: Optional[bool] = None


class SoftwareResponse(SoftwareBase):
    id: str
    # 安装配置
    software_type: Optional[str] = None
    package_format: Optional[str] = None
    storage_path: Optional[str] = None
    target_install_path: Optional[str] = None
    subfolder_name: Optional[str] = None
    silent_install_cmd: Optional[str] = None
    main_exe_relative_path: Optional[str] = None
    # 检测配置
    detection_method: Optional[str] = None
    detection_path: Optional[str] = None
    detection_keyword: Optional[str] = None
    # 其他
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SoftwareListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[SoftwareResponse]


# 用于任务下发时传递软件信息
class SoftwareForTask(BaseModel):
    """任务中包含的软件信息"""
    software_id: str
    software_code: str
    software_name: str
    software_type: str
    package_format: Optional[str] = None
    storage_path: Optional[str] = None
    target_install_path: Optional[str] = None
    subfolder_name: Optional[str] = None
    silent_install_cmd: Optional[str] = None
    main_exe_relative_path: Optional[str] = None
    detection_method: str
    detection_path: Optional[str] = None
    detection_keyword: Optional[str] = None
    version: Optional[str] = None

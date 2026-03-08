"""
数据保留策略 API
提供数据保留配置、统计和清理功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.data_retention_service import retention_service
from app.core.config import settings

router = APIRouter(prefix="/data-retention", tags=["Data Retention"])


class RetentionConfig(BaseModel):
    """数据保留配置"""

    metrics_retention_days: int = 30
    results_retention_days: int = 90
    audit_logs_retention_days: int = 180
    enable_auto_cleanup: bool = True
    cleanup_hour: int = 2
    metrics_collection_interval: int = 5


class CleanupRequest(BaseModel):
    """清理请求"""

    dry_run: bool = True


@router.get("/config", response_model=RetentionConfig)
def get_retention_config():
    """获取当前数据保留配置"""
    return {
        "metrics_retention_days": settings.metrics_retention_days,
        "results_retention_days": settings.results_retention_days,
        "audit_logs_retention_days": settings.audit_logs_retention_days,
        "enable_auto_cleanup": settings.enable_auto_cleanup,
        "cleanup_hour": settings.cleanup_hour,
        "metrics_collection_interval": settings.metrics_collection_interval,
    }


@router.get("/stats")
def get_retention_stats():
    """获取数据保留统计信息"""
    return retention_service.get_retention_stats()


@router.get("/sizes")
def get_data_sizes():
    """获取各表数据大小"""
    return retention_service.get_data_sizes()


@router.post("/cleanup")
def run_cleanup(request: CleanupRequest):
    """执行数据清理任务"""
    result = retention_service.run_cleanup(dry_run=request.dry_run)
    return result


@router.post("/cleanup/metrics")
def cleanup_metrics(dry_run: bool = True):
    """清理性能指标数据"""
    return retention_service.cleanup_performance_metrics(dry_run=dry_run)


@router.post("/cleanup/results")
def cleanup_results(dry_run: bool = True):
    """清理测试结果数据"""
    return retention_service.cleanup_test_results(dry_run=dry_run)


@router.post("/cleanup/audit-logs")
def cleanup_audit_logs(dry_run: bool = True):
    """清理审计日志数据"""
    return retention_service.cleanup_audit_logs(dry_run=dry_run)


@router.post("/cleanup/software-metrics")
def cleanup_software_metrics(dry_run: bool = True):
    """清理软件运行指标数据"""
    return retention_service.cleanup_software_metrics(dry_run=dry_run)


@router.post("/vacuum")
def vacuum_database():
    """VACUUM 数据库回收空间"""
    return retention_service.vacuum_database()


@router.get("/retention-options")
def get_retention_options():
    """获取可用的保留期限选项"""
    return {
        "metrics_retention_days_options": [3, 7, 14, 30, 60, 90],
        "results_retention_days_options": [7, 14, 30, 60, 90, 180, 365],
        "audit_logs_retention_days_options": [30, 60, 90, 180, 365, 730],
        "collection_interval_options": [1, 5, 10, 30, 60],
        "cleanup_hour_options": list(range(24)),
    }

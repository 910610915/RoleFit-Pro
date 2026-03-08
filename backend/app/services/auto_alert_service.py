"""
自动告警服务 - 根据阈值自动生成告警
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core.database import get_db_sync
from app.models.sqlite import PerformanceMetric, PerformanceAlert, Device

logger = logging.getLogger(__name__)


class AlertRule:
    """告警规则"""

    # 默认告警阈值
    DEFAULT_THRESHOLDS = {
        "cpu_percent": {"warning": 80.0, "critical": 95.0},
        "gpu_percent": {"warning": 85.0, "critical": 98.0},
        "memory_percent": {"warning": 85.0, "critical": 95.0},
        "cpu_temperature": {"warning": 80.0, "critical": 95.0},
        "gpu_temperature": {"warning": 83.0, "critical": 90.0},
        "disk_io_percent": {"warning": 90.0, "critical": 95.0},
        # 磁盘空间告警阈值 (百分比)
        "disk_space_percent": {"warning": 80.0, "critical": 90.0},
        # 内存绝对值告警阈值 (MB)
        "memory_available_mb": {
            "warning": 2048.0,
            "critical": 1024.0,
        },  # 可用内存低于此值告警
        # 网络丢包率
        "network_drop_percent": {"warning": 1.0, "critical": 5.0},
    }

    def __init__(self, metric_name: str, warning: float, critical: float):
        self.metric_name = metric_name
        self.warning = warning
        self.critical = critical

    def check(self, value: float, metric_name: str = None) -> Optional[str]:
        """检查值是否超过阈值，返回告警级别或None"""
        if value is None:
            return None

        # 反向阈值：当值低于阈值时告警（如磁盘空间、可用内存）
        inverse_metrics = {
            "memory_available_mb",
            "disk_space_percent",
            "network_drop_percent",
        }

        if metric_name and metric_name in inverse_metrics:
            # 值越低越危险
            if value <= self.critical:
                return "critical"
            elif value <= self.warning:
                return "warning"
        else:
            # 值越高越危险（传统方式）
            if value >= self.critical:
                return "critical"
            elif value >= self.warning:
                return "warning"
        return None


class AutoAlertService:
    """自动告警服务"""

    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        # 初始化默认规则
        for metric, thresholds in AlertRule.DEFAULT_THRESHOLDS.items():
            self.rules[metric] = AlertRule(
                metric, thresholds["warning"], thresholds["critical"]
            )

        # 告警冷却时间（秒）- 避免同一设备重复告警
        self.cooldown_seconds = 300  # 5分钟

    def check_metrics(
        self, device_id: str, metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """检查指标是否触发告警"""
        alerts = []

        for metric_name, rule in self.rules.items():
            # 获取指标值
            value = metrics.get(metric_name)

            if value is None:
                continue

            # 检查阈值（传入metric_name以处理反向阈值）
            severity = rule.check(value, metric_name)

            if severity:
                alert = {
                    "device_id": device_id,
                    "alert_type": f"high_{metric_name}",
                    "severity": severity,
                    "metric_name": metric_name,
                    "threshold_value": rule.warning
                    if severity == "warning"
                    else rule.critical,
                    "current_value": value,
                    "title": self._get_title(metric_name, severity),
                    "message": self._get_message(
                        metric_name,
                        value,
                        rule.warning if severity == "warning" else rule.critical,
                        severity,
                    ),
                }
                alerts.append(alert)

        return alerts

    def _get_title(self, metric_name: str, severity: str) -> str:
        """获取告警标题"""
        titles = {
            "cpu_percent": "CPU 使用率过高",
            "gpu_percent": "GPU 使用率过高",
            "memory_percent": "内存使用率过高",
            "cpu_temperature": "CPU 温度过高",
            "gpu_temperature": "GPU 温度过高",
            "disk_io_percent": "磁盘IO过高",
            "disk_space_percent": "磁盘空间不足",
            "memory_available_mb": "可用内存不足",
            "network_drop_percent": "网络丢包率过高",
        }
        prefix = "⚠️ 警告" if severity == "warning" else "🔴 严重"
        return f"{prefix} - {titles.get(metric_name, metric_name)}"

    def _get_message(
        self, metric_name: str, value: float, threshold: float, severity: str
    ) -> str:
        """获取告警消息"""
        level = "警告" if severity == "warning" else "严重"

        # 反向阈值消息
        inverse_metrics = {
            "memory_available_mb",
            "disk_space_percent",
            "network_drop_percent",
        }

        if metric_name in inverse_metrics:
            if metric_name == "memory_available_mb":
                return f"可用内存当前为 {value:.0f}MB，低于{level}阈值 {threshold:.0f}MB，请及时处理。"
            elif metric_name == "disk_space_percent":
                return f"磁盘使用率当前为 {value:.1f}%，超过{level}阈值 {threshold:.1f}%，请及时清理。"
            elif metric_name == "network_drop_percent":
                return f"网络丢包率当前为 {value:.2f}%，超过{level}阈值 {threshold:.2f}%，请检查网络。"

        return f"{metric_name} 当前值为 {value:.1f}，超过{level}阈值 {threshold:.1f}，请及时处理。"

    def create_alerts(self, alerts: List[Dict[str, Any]], db) -> int:
        """创建告警记录"""
        created_count = 0

        for alert_data in alerts:
            # 检查是否在冷却时间内已有未解决的相同告警
            from sqlalchemy import select

            query = select(PerformanceAlert).where(
                PerformanceAlert.device_id == alert_data["device_id"],
                PerformanceAlert.alert_type == alert_data["alert_type"],
                PerformanceAlert.is_resolved == False,
            )

            result = db.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                continue  # 跳过重复告警

            # 创建新告警
            alert = PerformanceAlert(**alert_data)
            db.add(alert)
            created_count += 1

        if created_count > 0:
            db.commit()

        return created_count


# 全局实例
auto_alert_service = AutoAlertService()


def check_and_create_alerts(device_id: str, metrics: Dict[str, Any], db) -> int:
    """检查指标并自动创建告警"""
    alerts = auto_alert_service.check_metrics(device_id, metrics)

    if alerts:
        return auto_alert_service.create_alerts(alerts, db)

    return 0

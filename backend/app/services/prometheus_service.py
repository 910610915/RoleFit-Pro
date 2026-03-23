"""
Prometheus 查询服务
用于从 Prometheus 获取监控数据

依赖:
    pip install prometheus

用法:
    from app.services.prometheus_service import prometheus_service

    # 查询单个指标
    data = prometheus_service.query('windows_cpu_percent{instance="DESKTOP-PC"}')

    # 查询范围数据
    from datetime import datetime, timedelta
    data = prometheus_service.query_range(
        query='windows_cpu_percent{instance="DESKTOP-PC"}',
        start_time=datetime.now() - timedelta(hours=1),
        end_time=datetime.now(),
        step='15s'
    )
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from prom import Prometheus

logger = logging.getLogger(__name__)


class PrometheusService:
    """Prometheus 查询服务"""

    def __init__(self):
        self.prometheus_url = os.environ.get("PROMETHEUS_URL", "http://localhost:9090")
        self.client = Prometheus(url=self.prometheus_url)
        self._available = None

    @property
    def is_available(self) -> bool:
        """检查 Prometheus 是否可用"""
        if self._available is None:
            try:
                self.client.query("up")
                self._available = True
            except Exception as e:
                logger.warning(f"Prometheus 不可用: {e}")
                self._available = False
        return self._available

    def query(self, query: str) -> List[Dict[str, Any]]:
        """
        执行即时查询

        Args:
            query: PromQL 查询语句

        Returns:
            查询结果列表
        """
        if not self.is_available:
            return []

        try:
            result = self.client.query(query)
            return self._parse_vector_result(result)
        except Exception as e:
            logger.error(f"Prometheus 查询失败: {e}")
            return []

    def query_range(
        self, query: str, start_time: datetime, end_time: datetime, step: str = "15s"
    ) -> List[Dict[str, Any]]:
        """
        执行范围查询

        Args:
            query: PromQL 查询语句
            start_time: 开始时间
            end_time: 结束时间
            step: 查询步长 (如 '15s', '1m', '5m')

        Returns:
            时间序列数据列表
        """
        if not self.is_available:
            return []

        try:
            # 转换为 Unix 时间戳（秒）
            start_ts = int(start_time.timestamp())
            end_ts = int(end_time.timestamp())

            result = self.client.query_range(
                query=query, start_time=start_ts, end_time=end_ts, step=step
            )
            return self._parse_matrix_result(result)
        except Exception as e:
            logger.error(f"Prometheus 范围查询失败: {e}")
            return []

    def get_current_value(self, query: str) -> Optional[float]:
        """
        获取当前值

        Args:
            query: 查询语句

        Returns:
            当前值，如果不存在返回 None
        """
        results = self.query(query)
        if results and len(results) > 0:
            try:
                return float(results[0]["value"])
            except (ValueError, TypeError):
                return None
        return None

    def get_cpu_percent(self, instance: str) -> Optional[float]:
        """获取 CPU 使用率"""
        return self.get_current_value(f'windows_cpu_percent{{instance="{instance}"}}')

    def get_memory_percent(self, instance: str) -> Optional[float]:
        """获取内存使用率"""
        return self.get_current_value(
            f'windows_memory_percent{{instance="{instance}"}}'
        )

    def get_gpu_percent(self, instance: str) -> Optional[float]:
        """获取 GPU 使用率"""
        return self.get_current_value(f'windows_gpu_percent{{instance="{instance}"}}')

    def get_gpu_temperature(self, instance: str) -> Optional[float]:
        """获取 GPU 温度"""
        return self.get_current_value(
            f'windows_gpu_temperature_celsius{{instance="{instance}"}}'
        )

    def get_cpu_temperature(self, instance: str) -> Optional[float]:
        """获取 CPU 温度"""
        return self.get_current_value(
            f'windows_cpu_temperature_celsius{{instance="{instance}"}}'
        )

    def get_cpu_history(self, instance: str, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取 CPU 使用率历史"""
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        return self.query_range(
            f'windows_cpu_percent{{instance="{instance}"}}', start, end, "15s"
        )

    def get_memory_history(
        self, instance: str, minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """获取内存使用率历史"""
        end = datetime.now()
        start = end - timedelta(minutes=minutes)
        return self.query_range(
            f'windows_memory_percent{{instance="{instance}"}}', start, end, "15s"
        )

    def get_gpu_history(
        self, instance: str, minutes: int = 60
    ) -> Dict[str, List[Dict[str, Any]]]:
        """获取 GPU 指标历史"""
        end = datetime.now()
        start = end - timedelta(minutes=minutes)

        utilization = self.query_range(
            f'windows_gpu_percent{{instance="{instance}"}}', start, end, "15s"
        )
        temperature = self.query_range(
            f'windows_gpu_temperature_celsius{{instance="{instance}"}}',
            start,
            end,
            "15s",
        )

        return {"utilization": utilization, "temperature": temperature}

    def get_latest_metrics(self, instance: str) -> Dict[str, Any]:
        """获取设备最新指标"""
        return {
            "instance": instance,
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": self.get_cpu_percent(instance),
            "memory_percent": self.get_memory_percent(instance),
            "gpu_percent": self.get_gpu_percent(instance),
            "gpu_temperature": self.get_gpu_temperature(instance),
            "cpu_temperature": self.get_cpu_temperature(instance),
        }

    def list_instances(self) -> List[str]:
        """列出所有监控实例"""
        results = self.query("windows_cpu_percent")
        instances = set()
        for item in results:
            instance = item.get("metric", {}).get("instance", "")
            if instance:
                instances.add(instance)
        return sorted(list(instances))

    def _parse_vector_result(self, result: Any) -> List[Dict[str, Any]]:
        """解析即时查询结果"""
        if not result:
            return []

        try:
            result_type = result.get("resultType")
            if result_type == "vector":
                return result.get("result", [])
            return []
        except Exception as e:
            logger.error(f"解析向量结果失败: {e}")
            return []

    def _parse_matrix_result(self, result: Any) -> List[Dict[str, Any]]:
        """解析范围查询结果"""
        if not result:
            return []

        try:
            result_type = result.get("resultType")
            if result_type == "matrix":
                return result.get("result", [])
            return []
        except Exception as e:
            logger.error(f"解析矩阵结果失败: {e}")
            return []


# 全局实例
prometheus_service = PrometheusService()

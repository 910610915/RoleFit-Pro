"""
WebSocket Service - 实时指标推送服务
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsWebSocketManager:
    """实时指标 WebSocket 管理器"""

    def __init__(self):
        # 设备ID -> WebSocket连接列表
        self.device_subscriptions: Dict[str, List[object]] = {}
        # 全局订阅者 (监控大屏)
        self.global_subscribers: List[object] = []

    async def connect(self, websocket, device_id: Optional[str] = None):
        """客户端连接"""
        if device_id:
            # 订阅特定设备
            if device_id not in self.device_subscriptions:
                self.device_subscriptions[device_id] = []
            self.device_subscriptions[device_id].append(websocket)
            logger.info(f"Client subscribed to device: {device_id}")
        else:
            # 全局订阅 (监控大屏)
            self.global_subscribers.append(websocket)
            logger.info("Client subscribed to global metrics")

    def disconnect(self, websocket):
        """客户端断开"""
        # 从设备订阅中移除
        for device_id, connections in list(self.device_subscriptions.items()):
            if websocket in connections:
                connections.remove(websocket)
                if not connections:
                    del self.device_subscriptions[device_id]

        # 从全局订阅中移除
        if websocket in self.global_subscribers:
            self.global_subscribers.remove(websocket)

    async def send_metrics(self, device_id: str, metrics: dict):
        """发送指标数据给订阅者"""
        message = {
            "type": "metrics",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": metrics,
        }

        # 发送给特定设备订阅者
        if device_id in self.device_subscriptions:
            for ws in self.device_subscriptions[device_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to device subscriber: {e}")

        # 发送给全局订阅者
        for ws in self.global_subscribers:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to global subscriber: {e}")

    async def send_alert(self, alert: dict):
        """发送告警"""
        message = {
            "type": "alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert,
        }

        # 发送给全局订阅者
        for ws in self.global_subscribers:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending alert: {e}")

    async def send_benchmark_update(self, device_id: str, benchmark: dict):
        """发送基准测试更新"""
        message = {
            "type": "benchmark_update",
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": benchmark,
        }

        # 发送给全局订阅者
        for ws in self.global_subscribers:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending benchmark update: {e}")


# 全局实例
metrics_ws_manager = MetricsWebSocketManager()


# 辅助函数：在接收到指标时调用
async def push_metrics(device_id: str, metrics: dict):
    """推送实时指标"""
    await metrics_ws_manager.send_metrics(device_id, metrics)


# 辅助函数：在创建告警时调用
async def push_alert(alert: dict):
    """推送告警"""
    await metrics_ws_manager.send_alert(alert)


# 辅助函数：在基准测试更新时调用
async def push_benchmark_update(device_id: str, benchmark: dict):
    """推送基准测试更新"""
    await metrics_ws_manager.send_benchmark_update(device_id, benchmark)

"""
WebSocket API - 实时任务进度更新
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 所有活跃连接
        self.active_connections: List[WebSocket] = []
        # 设备ID -> WebSocket 连接
        self.device_connections: Dict[str, WebSocket] = {}
        # 任务ID -> 订阅的客户端
        self.task_subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """客户端连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected: {client_id}, total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """客户端断开"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        # 清理设备连接
        for device_id, ws in list(self.device_connections.items()):
            if ws == websocket:
                del self.device_connections[device_id]
        # 清理任务订阅
        for task_id, connections in list(self.task_subscriptions.items()):
            if websocket in connections:
                connections.remove(websocket)
        logger.info(f"WebSocket client disconnected, remaining: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """发送消息给特定客户端"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
    
    def subscribe_task(self, task_id: str, websocket: WebSocket):
        """订阅任务进度"""
        if task_id not in self.task_subscriptions:
            self.task_subscriptions[task_id] = []
        if websocket not in self.task_subscriptions[task_id]:
            self.task_subscriptions[task_id].append(websocket)
    
    def unsubscribe_task(self, task_id: str, websocket: WebSocket):
        """取消订阅任务"""
        if task_id in self.task_subscriptions:
            if websocket in self.task_subscriptions[task_id]:
                self.task_subscriptions[task_id].remove(websocket)
    
    async def send_to_task_subscribers(self, task_id: str, message: dict):
        """发送消息给任务订阅者"""
        if task_id in self.task_subscriptions:
            for connection in self.task_subscriptions[task_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to task subscriber: {e}")


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点
    客户端连接后可订阅任务进度
    """
    client_id = None
    
    try:
        # 等待客户端消息来识别身份
        await websocket.accept()
        
        # 接收客户端的第一个消息来获取client_id
        try:
            first_message = await websocket.receive_json()
            client_id = first_message.get("client_id", "unknown")
            await manager.connect(websocket, client_id)
        except:
            await manager.connect(websocket, "anonymous")
        
        # 保持连接并处理消息
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "subscribe_task":
                    # 订阅任务
                    task_id = message.get("task_id")
                    if task_id:
                        manager.subscribe_task(task_id, websocket)
                        await websocket.send_json({
                            "type": "subscribed",
                            "task_id": task_id
                        })
                
                elif msg_type == "unsubscribe_task":
                    # 取消订阅
                    task_id = message.get("task_id")
                    if task_id:
                        manager.unsubscribe_task(task_id, websocket)
                
                elif msg_type == "ping":
                    # 心跳
                    await websocket.send_json({"type": "pong"})
                
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# 辅助函数：通知任务状态变化
async def notify_task_update(task_id: str, status: str, progress: int = 0, message: str = ""):
    """通知任务状态更新"""
    await manager.send_to_task_subscribers(task_id, {
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "message": message
    })


# 辅助函数：通知设备状态变化
async def notify_device_update(device_id: str, status: str, metrics: dict = None):
    """通知设备状态更新"""
    await manager.broadcast({
        "type": "device_update",
        "device_id": device_id,
        "status": status,
        "metrics": metrics or {}
    })

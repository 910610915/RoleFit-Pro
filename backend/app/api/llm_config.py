"""
LLM 配置管理 API

提供 LLM 配置的 CRUD 操作 - 简化版 (JSON文件存储)
"""

import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/llm-config", tags=["LLM Config"])

# Simple JSON file-based config storage
CONFIG_FILE = "llm_config.json"
CHAT_HISTORY_FILE = "chat_history.json"

def load_config():
    """Load config from JSON file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "provider": "siliconflow",
        "api_key": "",
        "model": "",
        "is_active": True,
        "status": "untested"
    }

def save_config(data):
    """Save config to JSON file"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat_history():
    """Load chat history from JSON file"""
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_chat_history(history):
    """Save chat history to JSON file"""
    with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ================================================
# Request/Response Models
# ================================================

class LLMConfigResponse(BaseModel):
    id: str
    provider: str
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_active: bool
    status: Optional[str] = "untested"


class LLMConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None


# ================================================
# API Endpoints
# ================================================

@router.get("/config", response_model=LLMConfigResponse)
async def get_llm_config():
    """获取当前 LLM 配置"""
    config = load_config()
    
    return LLMConfigResponse(
        id="1",
        provider=config.get("provider", "siliconflow"),
        api_key="***" if config.get("api_key") else None,
        model=config.get("model", ""),
        is_active=config.get("is_active", True),
        status=config.get("status", "untested")
    )


@router.post("/config", response_model=LLMConfigResponse)
async def save_llm_config(config_data: LLMConfigUpdate):
    """保存 LLM 配置"""
    config = load_config()
    
    if config_data.provider is not None:
        config["provider"] = config_data.provider
    if config_data.api_key is not None:
        config["api_key"] = config_data.api_key
    if config_data.model is not None:
        config["model"] = config_data.model
    if config_data.is_active is not None:
        config["is_active"] = config_data.is_active
    if config_data.status is not None:
        config["status"] = config_data.status
    
    save_config(config)
    
    return LLMConfigResponse(
        id="1",
        provider=config["provider"],
        api_key="***" if config.get("api_key") else None,
        model=config.get("model", ""),
        is_active=config.get("is_active", True),
        status=config.get("status", "untested")
    )


@router.post("/test")
async def test_provider_connection(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
):
    """测试提供商连接"""
    from app.services.llm_service import LLMProvider
    
    try:
        llm = LLMProvider(provider=provider, api_key=api_key)
        test_model = model or llm.default_model
        
        result = llm.chat(
            message="Hello, please reply with just your model name.",
            model=test_model,
            max_tokens=50
        )
        
        # Save test result status to config
        config = load_config()
        config["status"] = "ok"
        config["provider"] = provider
        if model:
            config["model"] = model
        save_config(config)
        
        return {
            "status": "ok",
            "model": result["model"],
            "response": result["content"][:200],
            "provider": provider
        }
    except Exception as e:
        # Save test result status to config
        config = load_config()
        config["status"] = "error"
        save_config(config)
        
        return {
            "status": "error",
            "error": str(e),
            "provider": provider
        }


# Chat history storage (file-based)
chat_history = {}


@router.get("/chat/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """获取对话历史"""
    history = load_chat_history()
    messages = history.get(session_id, [])
    return messages[-limit:]


@router.post("/chat/{session_id}")
async def send_chat_message(session_id: str, message: dict):
    """发送对话消息并保存"""
    from app.services.llm_service import LLMProvider
    
    config = load_config()
    
    # Load chat history from file
    history = load_chat_history()
    if session_id not in history:
        history[session_id] = []
    
    # Save user message
    user_msg = {
        "id": f"msg_{len(history[session_id]) + 1}",
        "session_id": session_id,
        "role": "user",
        "content": message.get("content", ""),
        "model": message.get("model", ""),
        "provider": message.get("provider", config.get("provider", "siliconflow")),
        "created_at": datetime.now().isoformat()
    }
    history[session_id].append(user_msg)
    
    # Call LLM
    try:
        provider_name = message.get("provider", config.get("provider", "siliconflow"))
        api_key = config.get("api_key") or message.get("api_key")
        
        llm = LLMProvider(provider=provider_name, api_key=api_key)
        
        # Build context from history
        messages_for_api = []
        for h in history[session_id][-10:]:
            messages_for_api.append({"role": h["role"], "content": h["content"]})
        
        result = llm.chat(
            message=message.get("content", ""),
            model=message.get("model") or config.get("model") or llm.default_model,
            messages=messages_for_api if len(messages_for_api) > 1 else None
        )
        
        # Save AI response
        assistant_msg = {
            "id": f"msg_{len(history[session_id]) + 1}",
            "session_id": session_id,
            "role": "assistant",
            "content": result["content"],
            "model": result["model"],
            "provider": provider_name,
            "created_at": datetime.now().isoformat()
        }
        history[session_id].append(assistant_msg)
        
        # Save to file
        save_chat_history(history)
        
        return assistant_msg
    except Exception as e:
        return {
            "error": str(e),
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }


@router.delete("/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """清除对话历史"""
    history = load_chat_history()
    if session_id in history:
        history[session_id] = []
        save_chat_history(history)
    
    return {"status": "ok", "message": "对话历史已清除"}
    
    return {"status": "ok", "message": "对话历史已清除"}

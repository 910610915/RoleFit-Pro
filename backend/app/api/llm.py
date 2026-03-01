"""
LLM API 接口

提供 AI 性能分析功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.llm_service import LLMProvider, get_llm_client

router = APIRouter(prefix="/api/llm", tags=["llm"])


# ================================================
# Request/Response Models
# ================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    provider: Optional[str] = None  # 指定提供商，不指定则使用默认
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]


class AnalyzeRequest(BaseModel):
    """性能分析请求"""
    hardware_info: Dict[str, Any]
    performance_data: Dict[str, Any]
    benchmark_data: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """性能分析响应"""
    bottleneck: str
    score_loss_percent: int
    upgrade_priority: List[str]
    estimated_improvement: str
    reasoning: str
    model: str
    provider: str
    usage: Dict[str, int]


# ================================================
# API Endpoints
# ================================================

@router.get("/providers", response_model=List[Dict[str, Any]])
async def get_providers():
    """
    获取可用 AI 提供商列表
    
    返回所有支持的 AI 提供商及其配置信息
    """
    return LLMProvider.get_available_providers()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    通用聊天接口
    
    向 AI 发送消息并获取回复
    """
    try:
        # 使用指定的提供商或默认
        provider_name = request.provider or "siliconflow"
        llm = LLMProvider(provider=provider_name)
        
        result = llm.chat(
            message=request.message,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return ChatResponse(
            content=result["content"],
            model=result["model"],
            provider=provider_name,
            usage=result["usage"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_performance(request: AnalyzeRequest):
    """
    性能分析接口
    
    分析硬件性能测试数据，输出瓶颈分析和升级建议
    
    请求示例:
    {
        "hardware_info": {
            "cpu_model": "i9-14900K",
            "gpu_model": "RTX 4090",
            "gpu_vram_mb": 24576,
            "ram_total_gb": 64,
            "disk_type": "NVMe"
        },
        "performance_data": {
            "avg_fps": 45.2,
            "min_fps": 28.1,
            "load_time_seconds": 15.3
        },
        "benchmark_data": {
            "target_fps": 60,
            "target_load_time": 8.5
        }
    }
    """
    try:
        # 使用指定的提供商或默认
        provider_name = request.provider or "siliconflow"
        llm = LLMProvider(provider=provider_name)
        
        result = llm.analyze_performance(
            hardware_info=request.hardware_info,
            performance_data=request.performance_data,
            benchmark_data=request.benchmark_data
        )
        
        return AnalyzeResponse(
            bottleneck=result.get("bottleneck", "unknown"),
            score_loss_percent=result.get("score_loss_percent", 0),
            upgrade_priority=result.get("upgrade_priority", []),
            estimated_improvement=result.get("estimated_improvement", "0%"),
            reasoning=result.get("reasoning", ""),
            model=result.get("model", ""),
            provider=provider_name,
            usage=result.get("usage", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能分析失败: {str(e)}")


@router.post("/chat/simple")
async def simple_chat(message: str, provider: Optional[str] = None):
    """
    简单聊天接口 (GET 参数)
    
    简化版聊天接口，只需要传入消息内容
    """
    try:
        llm = get_llm_client(provider)
        
        result = llm.chat(message=message)
        
        return {
            "content": result["content"],
            "model": result["model"],
            "provider": llm.provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================================================
# 测试接口
# ================================================

@router.get("/test")
async def test_llm():
    """
    测试 LLM 连接
    
    返回可用提供商列表和连接状态
    """
    providers = LLMProvider.get_available_providers()
    
    # 尝试连接默认提供商
    status = {}
    for p in providers:
        try:
            llm = LLMProvider(provider=p["id"])
            result = llm.chat(message="Hello", max_tokens=10)
            status[p["id"]] = {
                "status": "ok",
                "model": result["model"]
            }
        except Exception as e:
            status[p["id"]] = {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "providers": providers,
        "status": status,
        "default_provider": "siliconflow"
    }

"""
LLM 服务模块 - 支持多 AI 提供商

支持的提供商：
- 硅基流动 (SiliconFlow): https://api.siliconflow.cn/v1
- MiniMax: https://api.minimaxi.com/v1
- DeepSeek: https://api.deepseek.com/v1
- 智谱 AI: https://open.bigmodel.cn/api/paas/v4
- 通义千问: https://dashscope.aliyuncs.com/compatible-mode/v1
- OpenAI: https://api.openai.com/v1
"""

import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider:
    """AI 提供商配置"""
    
    # 提供商配置
    PROVIDERS = {
        "nvidia": {
            "name": "NVIDIA NIM",
            "base_url": "https://integrate.api.nvidia.com/v1",
            "default_model": "meta/llama-3.1-405b-instruct",
            "free": False,
            "models": [
                "meta/llama-3.1-405b-instruct",
                "meta/llama-3.1-70b-instruct",
                "meta/llama-3.1-8b-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct",
                "nvidia/llama-3.1-nemotron-70b-instruct-hf",
                "google/gemma-2-27b-it",
                "mistralai/mixtral-8x7b-instruct-v0.1",
            ]
        },
        "siliconflow": {
            "name": "硅基流动",
            "base_url": "https://api.siliconflow.cn/v1",
            "default_model": "Qwen/Qwen2.5-7B-Instruct",
            "free": True,
            "models": [
                "Qwen/Qwen2.5-7B-Instruct",
                "Qwen/Qwen2.5-Coder-7B-Instruct",
                "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
                "THUDM/glm-4-9b-chat",
                "internlm/internlm2_5-7b-chat",
            ]
        },
        "minimax": {
            "name": "MiniMax",
            "base_url": "https://api.minimaxi.com/v1",
            "default_model": "MiniMax-M2.5-highspeed",
            "free": False,
            "models": [
                "MiniMax-M2.5-highspeed",
                "MiniMax-M2.5",
                "MiniMax-M2.1",
            ]
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com",
            "default_model": "deepseek-chat",
            "free": False,
            "models": [
                "deepseek-chat",
                "deepseek-reasoner",
            ]
        },
        "zhipu": {
            "name": "智谱 AI",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4-flash",
            "free": True,
            "models": [
                "glm-4-flash",
                "glm-4-plus",
                "glm-4",
            ]
        },
        "qwen": {
            "name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-plus",
            "free": False,
            "models": [
                "qwen-plus",
                "qwen-turbo",
                "qwen-max",
            ]
        },
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-3.5-turbo",
            "free": False,
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
            ]
        },
    }
    
    def __init__(self, provider: str = "siliconflow", api_key: Optional[str] = None):
        """
        初始化 LLM 提供商
        
        Args:
            provider: 提供商名称 (siliconflow/minimax/deepseek/zhipu/qwen/openai/nvidia)
            api_key: API Key，如果不提供则使用配置中的默认 Key
        """
        self.provider = provider
        provider_config = self.PROVIDERS.get(provider)
        
        if not provider_config:
            raise ValueError(f"不支持的 AI 提供商: {provider}")
        
        self.base_url = provider_config["base_url"]
        # 优先使用 settings 中的模型配置
        self.default_model = settings.llm_model if settings.llm_model else provider_config["default_model"]
        self.name = provider_config["name"]
        
        # 使用提供的 API Key 或配置中的
        self.api_key = api_key or settings.llm_api_key
        
        # 创建 OpenAI 客户端 (兼容所有 OpenAI 格式的 API)
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=settings.llm_timeout
        )
    
    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        messages: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        发送聊天请求
        
        Args:
            message: 用户消息
            model: 模型名称 (可选，默认使用提供商的默认模型)
            system_prompt: 系统提示词 (可选)
            temperature: 温度参数
            max_tokens: 最大 Token 数
            messages: 完整的消息历史 (可选，用于上下文记忆)
            
        Returns:
            dict: {
                "content": "回复内容",
                "model": "使用的模型",
                "usage": {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}
            }
        """
        model = model or self.default_model
        
        # 如果提供了完整消息历史，直接使用
        if messages:
            # 添加当前消息
            messages.append({"role": "user", "content": message})
            chat_messages = messages
        else:
            # 构建简单消息
            chat_messages = []
            # 添加简洁回复的系统提示
            chat_messages.append({
                "role": "system", 
                "content": "你是一个有用的AI助手。请直接、简洁地回答用户的问题，不要添加不必要的解释或废话。如果需要，可以适当使用列表或简短段落。"
            })
            if system_prompt:
                chat_messages.append({"role": "system", "content": system_prompt})
            chat_messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                }
            }
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise
    
    def analyze_performance(
        self,
        hardware_info: Dict[str, Any],
        performance_data: Dict[str, Any],
        benchmark_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        分析硬件性能
        
        Args:
            hardware_info: 硬件信息
            performance_data: 性能测试数据
            benchmark_data: 标杆数据 (可选)
            
        Returns:
            dict: 分析结果
        """
        prompt = self._build_analysis_prompt(hardware_info, performance_data, benchmark_data)
        
        result = self.chat(
            message=prompt,
            system_prompt="你是一个专业的硬件性能分析专家。请分析以下测试数据并给出专业建议。"
        )
        
        # 尝试解析 JSON 响应
        try:
            analysis = json.loads(result["content"])
            return {
                **analysis,
                "model": result["model"],
                "usage": result["usage"]
            }
        except:
            # 如果不是 JSON，返回原始内容
            return {
                "bottleneck": "unknown",
                "score_loss_percent": 0,
                "upgrade_priority": [],
                "estimated_improvement": "0%",
                "reasoning": result["content"],
                "model": result["model"],
                "usage": result["usage"]
            }
    
    def _build_analysis_prompt(
        self,
        hardware_info: Dict[str, Any],
        performance_data: Dict[str, Any],
        benchmark_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建性能分析 Prompt"""
        
        prompt = f"""## 测试环境
- CPU: {hardware_info.get('cpu_model', 'Unknown')}
- GPU: {hardware_info.get('gpu_model', 'Unknown')}
- 显存: {hardware_info.get('gpu_vram_mb', 0) / 1024:.1f}GB
- 内存: {hardware_info.get('ram_total_gb', 0)}GB
- 磁盘: {hardware_info.get('disk_type', 'Unknown')}

## 性能数据
{json.dumps(performance_data, indent=2, ensure_ascii=False)}"""

        if benchmark_data:
            prompt += f"""

## 标杆数据（参考）
{json.dumps(benchmark_data, indent=2, ensure_ascii=False)}"""

        prompt += """

请分析以下内容：
1. 瓶颈识别：主要性能瓶颈在哪里？
2. 量化评估：与标杆机相比差距多少？
3. 升级建议：优先升级哪个硬件？
4. ROI 分析：升级后的预期改善

请以 JSON 格式输出：
{
  "bottleneck": "CPU/GPU/MEMORY/DISK",
  "score_loss_percent": 25,
  "upgrade_priority": ["GPU", "RAM"],
  "estimated_improvement": "30%",
  "reasoning": "详细分析理由"
}"""
        
        return prompt
    
    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        """获取可用提供商列表"""
        return [
            {
                "id": key,
                "name": config["name"],
                "default_model": config["default_model"],
                "free": config["free"],
                "models": config["models"]
            }
            for key, config in cls.PROVIDERS.items()
        ]


# 全局默认客户端
def get_llm_client(provider: Optional[str] = None) -> LLMProvider:
    """获取默认 LLM 客户端"""
    provider = provider or settings.llm_provider
    return LLMProvider(provider=provider)

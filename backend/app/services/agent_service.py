import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import LLMProvider
from app.core.tools import TOOLS_SCHEMA, AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: Session, provider: str = "siliconflow"):
        self.db = db
        # 允许 provider 为空，LLMProvider 会处理默认值
        self.llm = LLMProvider(provider=provider or "siliconflow")
        
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Agent 聊天核心逻辑 (支持 Function Calling)
        
        Args:
            message: 用户消息
            history: 历史对话记录
            
        Returns:
            Dict: {
                "content": "回复内容",
                "tool_calls": [...],  # 调试信息
                "usage": {...}
            }
        """
        # 1. 构建消息上下文
        messages = history if history else []
        
        # 添加系统提示词
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {
                "role": "system",
                "content": """你是一个专业的硬件性能测试助手 RoleFit Pro AI。
你的目标是帮助用户管理测试设备、运行性能测试任务并分析结果。

你可以使用提供的工具来获取系统数据。如果用户的问题需要查询数据，请务必调用工具。
如果工具返回了数据，请以 Markdown 表格的形式整理输出，并给出简短的分析或总结。
如果查询不到数据，请友好地告知用户。

不要编造数据，一切以工具返回的结果为准。"""
            })
            
        messages.append({"role": "user", "content": message})
        
        try:
            # 2. 第一次 LLM 调用 (Intent Recognition & Tool Selection)
            # 注意：OpenAI SDK 的 tools 参数格式
            response = self.llm.client.chat.completions.create(
                model=self.llm.default_model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",  # 让模型自己决定是否调用工具
                temperature=0.5
            )
            
            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls
            
            # 如果模型决定不调用工具，直接返回回复
            if not tool_calls:
                return {
                    "content": response_msg.content,
                    "tool_calls": [],
                    "usage": dict(response.usage)
                }
            
            # 3. 执行工具调用 (Tool Execution)
            messages.append(response_msg)  # 把 AI 的思考过程（含 tool_calls）加入历史
            
            executed_tools = []
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name in AVAILABLE_TOOLS:
                    logger.info(f"Executing tool: {function_name} args: {function_args}")
                    
                    # 执行函数
                    func = AVAILABLE_TOOLS[function_name]
                    try:
                        # 注入 db session
                        result = func(db=self.db, **function_args)
                        result_str = json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        result_str = f"Error: {str(e)}"
                    
                    # 记录执行结果
                    executed_tools.append({
                        "name": function_name,
                        "args": function_args,
                        "result": result
                    })
                    
                    # 将工具执行结果以 tool role 加入消息历史
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result_str
                    })
            
            # 4. 第二次 LLM 调用 (Result Synthesis)
            # 将工具结果喂回给 LLM，让它生成最终回复
            final_response = self.llm.client.chat.completions.create(
                model=self.llm.default_model,
                messages=messages,
                temperature=0.7
            )
            
            return {
                "content": final_response.choices[0].message.content,
                "tool_calls": executed_tools,
                "usage": dict(final_response.usage)
            }
            
        except Exception as e:
            logger.error(f"Agent chat failed: {e}")
            return {
                "content": f"抱歉，我遇到了一些问题: {str(e)}",
                "tool_calls": [],
                "usage": {}
            }

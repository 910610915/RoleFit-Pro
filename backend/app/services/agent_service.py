import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.llm_service import LLMProvider
from app.core.tools import TOOLS_SCHEMA, AVAILABLE_TOOLS

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, db: Session, provider: str = "siliconflow", api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        self.db = db
        # 允许 provider 为空，LLMProvider 会处理默认值
        self.llm = LLMProvider(provider=provider or "siliconflow", api_key=api_key)
        if model:
            self.llm.default_model = model
        if base_url:
            self.llm.client.base_url = base_url
            self.llm.base_url = base_url
        
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
如果用户提到某个特定的设备（如“俊爷的电脑”），请优先使用 get_devices(keyword="...") 工具来查找该设备。
注意：在使用 keyword 搜索时，请提取最核心的名称（例如用户说“俊爷的电脑”，请只搜索“俊爷”），不要包含“的电脑”、“设备”等冗余词汇，以提高匹配率。

如果工具返回了数据，请以 Markdown 表格的形式整理输出，并给出简短的分析或总结。
如果查询不到数据，请友好地告知用户，并列出你尝试搜索的关键词。

不要编造数据，一切以工具返回的结果为准。"""
            })
            
        messages.append({"role": "user", "content": message})
        
        try:
            # 2. 第一次 LLM 调用 (Intent Recognition & Tool Selection)
            logger.info(f"Agent Chat Request: {message}")
            logger.info(f"Using Model: {self.llm.default_model}")
            
            response = self.llm.client.chat.completions.create(
                model=self.llm.default_model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                temperature=0.5
            )
            
            response_msg = response.choices[0].message
            tool_calls = response_msg.tool_calls
            
            # 如果模型决定不调用工具，直接返回回复
            if not tool_calls:
                content = response_msg.content
                if not content:
                    content = "🤔 AI 似乎在思考，但没有输出任何内容（可能是模型未触发工具调用）。"
                
                return {
                    "content": content,
                    "tool_calls": [],
                    "usage": dict(response.usage) if response.usage else {}
                }
            
            # 3. 执行工具调用 (Tool Execution)
            # 注意：如果不把 tool_calls 加入历史，第二次调用会报错
            messages.append(response_msg)
            
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
                        result_str = json.dumps({"error": str(e)}, ensure_ascii=False)
                    
                    # 记录执行结果
                    executed_tools.append({
                        "name": function_name,
                        "args": function_args,
                        "result": result_str
                    })
                    
                    # 将工具执行结果以 tool role 加入消息历史
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": result_str
                    })
            
            # 4. 第二次 LLM 调用 (Result Synthesis)
            final_response = self.llm.client.chat.completions.create(
                model=self.llm.default_model,
                messages=messages,
                temperature=0.7
            )
            
            final_content = final_response.choices[0].message.content
            # 兜底：如果最终回复为空，智能生成总结
            if not final_content:
                if executed_tools:
                    final_content = ""
                    for tool in executed_tools:
                        name = tool['name']
                        result = tool['result']
                        args = tool['args']
                        
                        if name == "get_devices":
                            if isinstance(result, list) and result:
                                final_content += f"🔍 **查询到 {len(result)} 台设备：**\n"
                                for dev in result:
                                    status_icon = "🟢" if dev.get('status') == 'online' else "🔴"
                                    final_content += f"\n{status_icon} **{dev.get('name')}**\n"
                                    final_content += f"- CPU: {dev.get('cpu')}\n"
                                    final_content += f"- GPU: {dev.get('gpu')}\n"
                                    final_content += f"- 内存: {dev.get('ram')}\n"
                            else:
                                final_content += f"🔍 未找到符合条件的设备 (关键词: {args.get('keyword')})\n"
                                
                        elif name == "get_tasks":
                            final_content += "📋 **测试任务列表：**\n"
                            if isinstance(result, list) and result:
                                for task in result:
                                    final_content += f"- [{task.get('status')}] {task.get('name')} ({task.get('type')})\n"
                            else:
                                final_content += "暂无任务记录。\n"
                                
                        elif name == "get_results":
                            final_content += "📊 **测试结果：**\n"
                            if isinstance(result, list) and result:
                                for res in result:
                                    final_content += f"- {res.get('device')}: {res.get('score')}分 ({res.get('test_type')})\n"
                            else:
                                final_content += "暂无测试结果。\n"
                                
                        elif name == "get_device_metrics":
                            final_content += "📈 **性能监控数据：**\n"
                            if isinstance(result, list) and result and not result[0].get('error'):
                                for m in result:
                                    final_content += f"- [{m.get('time')}] CPU: {m.get('cpu_load')} | GPU: {m.get('gpu_load')} | RAM: {m.get('ram_usage')}\n"
                            else:
                                msg = result[0].get('error') or result[0].get('message') if result else "无数据"
                                final_content += f"{msg}\n"
                        
                        else:
                            # 其他工具，显示原始 JSON
                            result_str = str(result)
                            if len(result_str) > 500:
                                result_str = result_str[:500] + "..."
                            final_content += f"\n🔧 **{name}**:\n```json\n{result_str}\n```\n"
                else:
                    final_content = "🤔 AI 似乎没有返回内容。"

            return {
                "content": final_content,
                "tool_calls": executed_tools,
                "usage": dict(final_response.usage) if final_response.usage else {}
            }
            
        except Exception as e:
            logger.error(f"Agent chat failed: {e}", exc_info=True)
            logger.error(f"Context: Provider={self.llm.provider}, Model={self.llm.default_model}, BaseURL={self.llm.base_url}")
            return {
                "content": f"⚠️ AI 服务暂时不可用: {str(e)}",
                "tool_calls": [],
                "usage": {},
                "error": True
            }

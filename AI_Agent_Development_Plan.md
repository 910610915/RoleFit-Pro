# RoleFit Pro AI Agent 增强开发文档 (Function Calling)

## 1. 概述

本项目旨在将 RoleFit Pro 现有的 "基于规则匹配 (If-Else)" 的 AI 聊天功能，升级为 "基于函数调用 (Function Calling)" 的真 AI Agent。通过引入 Function Calling 机制，让 LLM (大语言模型) 能够理解用户的自然语言指令，并自主决策调用系统的 API（如查询设备、执行测试、分析报告等），从而实现真正的智能交互。

### 1.1 核心目标

*   **移除硬编码规则**：废弃前端 `AIChatDrawer.vue` 中死板的关键词匹配逻辑。
*   **自然语言交互**：支持用户使用任意自然语言（如 "帮我看看哪些机器闲着"、"测试一下 4090 的性能"）进行操作。
*   **自主工具调用**：后端 AI 服务能够根据语义，自动选择并调用合适的业务函数（Tools）。
*   **结构化输出**：AI 的回复不再仅仅是文本，而是包含操作结果的结构化数据（如 JSON、Markdown 表格）。

---

## 2. 架构设计

### 2.1 交互流程

1.  **用户输入**：前端接收用户消息（例如："查询所有在线设备"）。
2.  **发送请求**：前端将消息直接发送给后端 `/api/llm/agent/chat` 接口。
3.  **意图识别与工具选择 (LLM)**：
    *   后端 LLM 服务接收消息，结合已注册的 **工具描述 (Tools Definition)**。
    *   LLM 分析语义，判断是否需要调用工具。
    *   如果需要，LLM 返回 **工具调用请求 (Function Call Request)**（包含函数名和参数）。
4.  **工具执行 (Backend)**：
    *   后端代码捕获工具调用请求。
    *   执行对应的 Python 业务函数（如 `get_device_list(status='online')`）。
    *   获取执行结果（JSON 数据）。
5.  **结果生成 (LLM)**：
    *   后端将 **工具执行结果** 再次喂给 LLM。
    *   LLM 根据执行结果，生成最终的自然语言回复（或 Markdown 格式的报表）。
6.  **前端渲染**：前端接收最终回复并渲染。

### 2.2 核心模块

*   **`app.services.agent_service.py`**: 新增 Agent 服务，负责管理工具集、与 LLM 交互、执行工具调用。
*   **`app.core.tools.py`**: 定义所有开放给 AI 的工具函数（Tools），包含函数实现和 Schema 描述。
*   **`app.api.agent.py`**: 新增 Agent 相关的 API 路由。

---

## 3. 详细设计

### 3.1 工具定义 (Tools Schema)

我们将开放以下核心能力给 AI：

| 工具名称 | 函数名 | 描述 | 参数示例 |
| :--- | :--- | :--- | :--- |
| **设备查询** | `get_devices` | 根据条件查询设备列表 | `{"status": "online", "gpu_model": "RTX 4090"}` |
| **设备状态** | `get_device_status` | 获取指定设备的详细状态 | `{"device_name": "PC-001"}` |
| **性能监控** | `get_performance` | 获取设备的实时性能数据 | `{"device_name": "PC-001"}` |
| **任务管理** | `list_tasks` | 查询测试任务列表 | `{"status": "running", "limit": 5}` |
| **创建任务** | `create_task` | 创建新的测试任务 | `{"device_name": "PC-001", "script_name": "3DMark"}` |
| **软件查询** | `list_software` | 查询支持的软件列表 | `{"category": "render"}` |

### 3.2 数据结构

#### 3.2.1 工具描述格式 (OpenAI Standard)

```json
{
  "type": "function",
  "function": {
    "name": "get_devices",
    "description": "查询设备列表，支持按状态、部门、显卡型号等条件筛选",
    "parameters": {
      "type": "object",
      "properties": {
        "status": {
          "type": "string",
          "enum": ["online", "offline", "busy", "idle"],
          "description": "设备状态"
        },
        "gpu_model": {
          "type": "string",
          "description": "显卡型号关键词，如 '4090', '3080'"
        }
      },
      "required": []
    }
  }
}
```

#### 3.2.2 聊天接口定义

**Endpoint**: `POST /api/llm/agent/chat`

**Request**:
```json
{
  "message": "帮我查一下现在有哪些在线的 4090 显卡机器",
  "history": [...] // 可选，历史对话上下文
}
```

**Response**:
```json
{
  "content": "为您找到 3 台在线的 RTX 4090 设备：\n\n| 设备名 | 状态 | 显存 | ...",
  "tool_calls": [ ... ], // 调试用，显示 AI 调用了什么工具
  "usage": { ... }
}
```

---

## 4. 开发步骤

### 第一阶段：后端基础建设 (Backend) - [Completed]

1.  **创建工具库 (`app/core/tools.py`)**：
    *   实现 `get_devices`, `get_device_status` 等 Python 函数。
    *   使用装饰器或手动编写对应的 JSON Schema 描述。

2.  **实现 Agent 逻辑 (`app/services/agent_service.py`)**：
    *   封装 LLM 调用逻辑，支持 `tools` 参数。
    *   实现 "思考-调用-再思考" 的循环逻辑（ReAct 模式或 Function Calling 模式）。

3.  **暴露 API (`app/api/agent.py`)**：
    *   创建 `/api/llm/agent/chat` 接口。

### 第二阶段：前端对接 (Frontend) - [Completed]

1.  **更新 API 客户端 (`frontend/src/api/ai.ts`)**：
    *   新增 `agentChat` 方法。

2.  **重构聊天组件 (`frontend/src/components/AIChatDrawer.vue`)**：
    *   **删除**原有的 `handleIntent` 正则匹配逻辑。
    *   **修改**发送逻辑，直接调用 `agentChat`。
    *   **优化**消息渲染，支持 Markdown 表格和代码块的高亮显示（AI 返回的数据通常是 Markdown 格式）。

### 第三阶段：配置与优化 (Configuration & UX) - [Completed]

1.  **自定义 AI 提供商**：
    *   在前端添加配置界面，支持自定义 Base URL、API Key 和模型名称。
    *   后端支持动态接收前端传递的配置参数。
    *   **新增**：支持自定义厂商名称，支持本地 LLM (Ollama) 预设。

2.  **UI/UX 优化**：
    *   解决悬浮按钮遮挡输入框的问题。
    *   移除旧版 AI 功能入口。
    *   **新增**：使用 DiceBear 替换默认图标，提升视觉体验。

3.  **连接测试**：
    *   后端新增 `/api/llm/test` 接口。
    *   前端设置面板增加“测试连接”按钮。

---

## 5. 预期效果示例

**用户**： "最近有没有什么任务失败了？"

**旧版 (If-Else)**： *(无法识别，因为没有匹配到 '任务列表' 关键词)* -> "抱歉，我没听懂..."

**新版 (Agent)**：
1.  **AI 思考**：用户想看失败的任务 -> 调用 `list_tasks(status='failed', limit=5)`。
2.  **系统执行**：查询数据库，返回最近 3 条失败记录。
3.  **AI 回复**： "最近有 3 个任务执行失败：
    1. **Task-001** (PC-A): 3DMark 测试超时
    2. **Task-005** (PC-B): 显存不足
    3. ...
    建议您检查这些设备的连接状态。"

---

## 6. 技术栈要求

*   **Backend**: Python 3.10+, FastAPI, OpenAI SDK (兼容各大模型厂商)
*   **LLM Provider**: 推荐使用 **DeepSeek-V3** (性价比高，Function Calling 能力强) 或 **Qwen-Max**。
*   **Frontend**: Vue 3, Naive UI, Markdown-it (渲染)

# 3D 软件自动化性能监测与客观评估方案

## 1. 核心背景与痛点

目前对员工电脑性能的评估仅依赖于任务管理器的实时占用率（CPU/GPU/RAM），缺乏**客观性**和**业务相关性**。

* **痛点：** 硬件占用高不代表卡顿，低占用也不代表流畅；由于项目复杂度不同，员工的主观感受难以作为硬件升级的唯一标准。

---

## 2. 总体思路

通过 **Python 脚本自动化控制 3D 软件**，在完全一致的测试环境下执行预设的高强度业务动作，采集底层硬件响应数据，最终通过 **LLM（大模型）** 进行专家级的瓶颈分析。

---

## 3. 技术架构：原子化动作库方案

为了保证稳定性与低成本，采用"工具调用（Function Calling）"逻辑，而非让 AI 盲目编写代码。

### A. 基础设施层 (Python)

* **环境隔离：** 脚本运行前将原始项目复制到系统的 `Temp` 目录，确保对生产资产**零污染、零风险**。
* **硬件探针：** 利用 `psutil` 和 `GPUtil` 实时监控物理指标（频率，温度、显存溢出状态）。

### B. 3D 执行层 (Software API)

预设四大基准测试模块：

1. **加载测试：** 记录大型项目从硬盘载入内存的总时长。
2. **交互测试：** 自动化旋转视口、缩放，平移，监测 **1% Low FPS**（衡量瞬间卡顿感）。
3. **计算测试：** 运行物理模拟（布料、粒子）或高面数细分，测试 CPU/GPU 峰值性能。
4. **压力测试：** 持续高负载运行 15 分钟，监测是否存在**热降频（Thermal Throttling）**导致的性能衰减。

---

## 4. 游戏开发软件自动化支持情况

### 4.1 软件分类与自动化能力

| 软件类型 | 软件名称 | API/脚本支持 | 推荐控制方式 | 优先级 |
|----------|----------|--------------|--------------|--------|
| **3D 建模** | Blender | 完整 Python API | 内置 Python | 最高 |
| **3D 建模** | Maya | OpenMaya Python API | 内置 Python | 最高 |
| **3D 建模** | 3ds Max | MAXScript + Python | 内置脚本 | 最高 |
| **3D 建模** | Cinema 4D | Python API | 内置 Python | 最高 |
| **游戏引擎** | Unreal Engine | Python + Blueprint | 命令行/API | 最高 |
| **游戏引擎** | Unity | Python Editor Scripting | Python + 命令行 | 最高 |
| **游戏引擎** | Godot | MCP 协议 | MCP Server | 高 |
| **材质/纹理** | Substance Painter | 有限 | 命令行/API | 高 |
| **材质/纹理** | Substance Designer | 有限 | 命令行 | 高 |
| **视频编辑** | Premiere Pro | ExtendScript | COM/脚本 | 高 |
| **视频编辑** | DaVinci Resolve | Python API | Fusion API | 高 |
| **特效合成** | After Effects | ExtendScript | COM/脚本 | 一般 |
| **特效合成** | Nuke | Python API | 内置 Python | 高 |
| **特效合成** | Houdini | Python API | 内置 Python | 高 |
| **图像处理** | Photoshop | ExtendScript | COM/脚本 | 一般 |
| **版本管理** | Perforce | P4Python API | Python | 高 |

### 4.2 支持自动化的软件（优先开发）

#### Blender（优先级最高）
- **Python API**: `bpy` 模块，完全内置
- **控制方式**: 直接 `import bpy` 即可控制
- **测试场景**: 场景加载、渲染、粒子模拟、几何节点
- **示例操作**:
```python
import bpy
import time

# 加载测试
start = time.time()
bpy.ops.wm.open(filepath="test.blend")
load_time = time.time() - start

# 渲染测试
bpy.ops.render.render()
```

#### Maya（优先级最高）
- **Python API**: `pymel`, `maya.cmds`, `OpenMaya`
- **控制方式**: `mayapy.exe` 或 `maya -command`
- **测试场景**: 场景加载、动画播放、渲染

#### Unreal Engine（优先级最高）
- **控制方式**: `UAT (Unreal Automation Tool)` + Python Editor Scripts
- **命令行**: `ue4editor.exe -run=UnitTest`
- **测试场景**: 蓝图编译、着色器编译、PIE启动

#### Unity（优先级最高）
- **Python API**: `UnityEditor.Scripting.Python`
- **控制方式**: 命令行 + Python 脚本
- **测试场景**: 场景加载、脚本编译、Build

### 4.3 不支持自动化的软件（替代方案）

对于没有官方 Python API 的软件（如 Photoshop、After Effects），采用以下替代方案：

| 替代方案 | 描述 | 适用场景 | 稳定性 |
|----------|------|----------|--------|
| **PyAutoGUI** | 纯 UI 自动化 | 简单操作 | 低 |
| **pywinauto** | Windows UI 自动化 | 复杂窗口操作 | 中 |
| **UI automation** | Windows 原生 UI 框架 | 精准定位 | 中 |
| **RPA** | 企业级自动化工具 | 复杂流程 | 高 |
| **Image Recognition** | 图像识别定位 | 无窗口句柄 | 中 |
| **OCR 识别** | 文字识别辅助 | UI 文本验证 | 中 |

#### 推荐方案：分层控制策略

```
测试任务调度层
    |
有API软件层  |  无API软件层
(Blender)    |  (PyAutoGUI + 图像识别)
    |
硬件数据采集层 (psutil + GPUtil + nvidia-smi)
```

---

## 5. AI 大模型接入方案

### 5.1 架构选型：集成到项目内部

**推荐方案：直接集成到 RoleFit Pro 后端**

#### 理由：
1. **无需额外部署**：AI 功能直接集成在项目中
2. **灵活切换**：通过配置文件切换不同 AI 提供商
3. **统一管理**：所有 AI 调用通过项目配置管理
4. **零额外成本**：不占用额外服务器资源

#### 支持的 AI 提供商

| 提供商 | 模型列表 | 特点 |
|--------|----------|------|
| **硅基流动** | Qwen/Qwen2.5-7B-Instruct, DeepSeek-R1 等 | 免费模型多 |
| **MiniMax** | M2.5-highspeed, M2.5, M2.1 | Coding Plan 优惠 |
| **DeepSeek** | deepseek-chat, deepseek-reasoner | 性价比高 |
| **智谱 AI** | glm-4-flash, glm-4-plus | 免费额度 |
| **通义千问** | qwen-plus, qwen-turbo, qwen-max | 阿里生态 |
| **OpenAI** | gpt-4o, gpt-3.5-turbo | 国际模型 |

#### 系统架构

```
┌─────────────────────────────────────────────────────┐
│              RoleFit Pro 后端                        │
│    FastAPI + SQLite + LLM Service                  │
├─────────────────────────────────────────────────────┤
│              LLM 服务层                              │
│    ┌─────────────────────────────────────────────┐ │
│    │  LLMProvider 类                              │ │
│    │  - siliconflow / minimax / deepseek        │ │
│    │  - zhipu / qwen / openai                   │ │
│    │  - 统一接口 + Prompt 模板                   │ │
│    └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│              API 接口                                │
│    GET  /api/llm/providers   获取可用提供商       │
│    POST /api/llm/chat        通用聊天             │
│    POST /api/llm/analyze     性能分析             │
│    GET  /api/llm/test        测试连接             │
└─────────────────────────────────────────────────────┘
```

### 5.2 LLM 分析 Prompt 模板

```python
ANALYSIS_PROMPT = """
你是硬件性能分析专家。请分析以下测试数据并给出专业建议。

## 测试环境
- 测试软件: {software_name}
- 测试场景: {test_scenario}
- 测试时间: {test_duration}s

## 硬件配置
- CPU: {cpu_model}
- GPU: {gpu_model}
- 显存: {vram_gb}GB
- 内存: {ram_gb}GB

## 性能数据
{performance_data_json}

## 标杆数据（参考）
{benchmark_data_json}

请分析以下内容：
1. 瓶颈识别：主要性能瓶颈在哪里？
2. 量化评估：与标杆机相比差距多少？
3. 升级建议：优先升级哪个硬件？
4. ROI 分析：升级后的预期改善

## 输出格式
请以 JSON 格式输出：
{
  "bottleneck": "CPU/GPU/MEMORY/DISK",
  "score_loss_percent": 25,
  "upgrade_priority": ["GPU", "RAM"],
  "estimated_improvement": "30%",
  "reasoning": "详细分析理由"
}
"""
```

### 5.3 后端配置

#### 环境变量 (.env)

```bash
# 当前使用的 AI 提供商
# 可选值: siliconflow, minimax, deepseek, zhipu, qwen, openai
LLM_PROVIDER=siliconflow

# API Key (从对应 AI 提供商获取)
LLM_API_KEY=your-api-key-here

# 默认模型
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct

# 请求超时时间
LLM_TIMEOUT=60
```

### 5.4 API 接口

系统已内置以下 API 接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/llm/providers` | GET | 获取可用 AI 提供商列表 |
| `/api/llm/chat` | POST | 通用聊天接口 |
| `/api/llm/analyze` | POST | 性能分析接口 |
| `/api/llm/test` | GET | 测试 LLM 连接 |

### 5.5 快速开始

#### 1. 配置 API Key

在 `backend/.env` 文件中添加：

```bash
LLM_PROVIDER=siliconflow
LLM_API_KEY=从 https://www.siliconflow.cn 获取的 API Key
```

#### 2. 安装依赖

```bash
pip install openai
```

#### 3. 测试连接

访问 `GET /api/llm/test` 查看连接状态

---

## 6. 数据采集规范

### 6.1 性能指标清单

| 指标类别 | 具体指标 | 采集方式 | 数据类型 |
|----------|----------|----------|----------|
| **时间指标** | 加载时长 | Python time.time() | float (秒) |
| **帧率指标** | 平均 FPS | 渲染 API / 计时 | float |
| **帧率指标** | 1% Low FPS | 帧时间统计 | float |
| **帧率指标** | 帧时间波动 | 标准差 | float |
| **CPU 指标** | 使用率 | psutil.cpu_percent() | float (%) |
| **CPU 指标** | 频率 | psutil.cpu_freq() | float (MHz) |
| **CPU 指标** | 温度 | wmi | float (℃) |
| **GPU 指标** | 使用率 | pynvml / GPUtil | float (%) |
| **GPU 指标** | 显存使用 | pynvml | int (MB) |
| **GPU 指标** | GPU 温度 | pynvml | float (℃) |
| **GPU 指标** | 功耗 | pynvml | float (W) |
| **内存指标** | 使用量 | psutil.virtual_memory() | int (MB) |
| **内存指标** | 峰值使用 | 统计 | int (MB) |
| **磁盘指标** | 读取速度 | psutil.disk_io_counters() | int (MB/s) |
| **磁盘指标** | 写入速度 | psutil.disk_io_counters() | int (MB/s) |

### 6.2 数据格式定义 (JSON Schema)

```json
{
  "test_session": {
    "session_id": "uuid",
    "software": "blender",
    "version": "4.0",
    "scenario": "scene_load",
    "start_time": "2026-02-27T10:00:00Z",
    "duration_seconds": 120
  },
  "hardware": {
    "cpu": {"model": "i9-14900K", "cores": 24, "threads": 32},
    "gpu": {"model": "RTX 4090", "vram_gb": 24},
    "ram": {"total_gb": 64},
    "disk": {"model": "990 PRO", "type": "NVMe"}
  },
  "metrics": {
    "timeline": [
      {"timestamp": 0, "cpu_percent": 45, "gpu_percent": 78, "fps": 60},
      {"timestamp": 1, "cpu_percent": 52, "gpu_percent": 82, "fps": 58}
    ],
    "summary": {
      "avg_fps": 58.5,
      "min_fps": 42.1,
      "low_1pct_fps": 48.2,
      "avg_cpu": 55.2,
      "avg_gpu": 80.5,
      "peak_vram_mb": 18432
    }
  }
}
```

---

## 7. 与现有系统集成

### 7.1 数据流设计

```
Agent采集  ->  后端存储  ->  LLM分析
硬件+性能      SQLite       瓶颈诊断
                    |
                前端展示
                报告生成
```

### 7.2 复用现有模块

| 现有模块 | 复用方式 |
|----------|----------|
| FeatureCard | 新增"性能测试"卡片 |
| TestTask | 扩展任务类型支持自动化测试 |
| TestResult | 扩展存储自动化测试结果 |
| Device | 关联性能测试历史 |

---

## 8. 实施路线图

| 阶段 | 关键任务 | 预期产出 |
|------|----------|----------|
| 第一阶段：基准抓取 | 运行一键硬件抓取脚本 | 建立全公司员工硬件资产库 |
| 第二阶段：脚本开发 | 开发针对 Blender/Maya 的原子动作库 | 形成标准化的测试工具包 |
| 第三阶段：Agent 接入 | 对接 LLM 接口，编写分析 Prompt | 实现"输入数据 -> 输出诊断结果"的闭环 |
| 第四阶段：常态化巡检 | 定期对核心开发电脑进行性能"年检" | 产出年度硬件优化建议报告 |

### MVP 版本范围（第一版本）

| 功能 | 范围 |
|------|------|
| 支持软件 | Blender (开源,API完善) |
| 测试场景 | 场景加载、简单渲染 |
| 硬件采集 | CPU/GPU/内存/磁盘 |
| LLM 分析 | 基础瓶颈识别 + 升级建议 |
| 数据存储 | 复用现有 SQLite |

---

## 9. 安全与风险控制

* **数据安全：** 脚本执行 `quit(save=False)`，强制不保存任何更改。
* **性能隔离：** 临时副本机制，保证原始 .blend / .mb 文件不被占用或损坏。
* **资源回收：** 测试完毕后自动杀掉残留进程，清空临时缓存，不占用员工硬盘空间。
* **权限控制：** 需要管理员权限来结束进程和访问硬件信息

---

## 10. 后续扩展方向

* **全模态接入：** 引入视觉模型识别屏幕渲染是否出现花屏、掉帧或 UI 渲染错误。
* **自动化资产体检：** 不仅查电脑，也查项目。自动揪出面数过高、贴图过大的"违规资产"。
* **多软件支持：** 扩展到 Maya、3ds Max、Unity、Unreal Engine
* **本地 LLM：** 集成 Ollama 支持本地部署，保护数据隐私

---

## 附录 A：软件版本检测命令

```python
# Blender
bpy.app.version_string  # "4.0.2"

# Maya
import maya.cmds as cmds
cmds.about(version=True)

# Unreal Engine
# 通过命令行: ue4 -version

# Unity
# 通过命令行: unity -version
```

## 附录 B：标杆数据示例

```json
{
  "blender_scene_load": {
    "target_hardware": "RTX 4090 + i9-14900K + 64GB",
    "reference_time_seconds": 8.5,
    "reference_fps": 60
  },
  "maya_scene_load": {
    "target_hardware": "RTX 4090 + i9-14900K + 64GB",
    "reference_time_seconds": 12.3
  }
}
```

## 附录 C：推荐模型配置

### 推荐模型列表（按场景）

| 场景 | 推荐模型 | 提供商 | 特点 |
|------|----------|--------|------|
| **代码生成** | MiniMax-M2.5-highspeed | MiniMax | Coding Plan 专属，性价比高 |
| **代码生成** | Qwen2.5-Coder-7B-Instruct | 硅基流动 | 免费，开源 |
| **通用对话** | deepseek-chat | DeepSeek | 便宜好用 |
| **通用对话** | qwen-max | 阿里通义 | 稳定可靠 |
| **长文本分析** | GLM-4-9B-Chat | 智谱 AI | 免费额度 |
| **复杂推理** | deepseek-reasoner | DeepSeek | R1 推理能力强 |

### 切换提供商

在 `backend/.env` 中修改配置即可切换：

```bash
# 硅基流动
LLM_PROVIDER=siliconflow
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_API_KEY=your-siliconflow-key

# 或切换到 MiniMax
LLM_PROVIDER=minimax
LLM_MODEL=MiniMax-M2.5-highspeed
LLM_API_KEY=your-minimax-key

# 或切换到 DeepSeek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_API_KEY=your-deepseek-key
```

### 使用建议

1. **开发测试阶段**：使用硅基流动的免费模型
2. **生产环境**：切换到 MiniMax Coding Plan 或 DeepSeek
3. **代码中切换**：调用 API 时指定 provider 参数即可

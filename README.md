# RoleFit Pro

Intelligent Hardware Performance Benchmark and Position Matching Platform

## 简介

**RoleFit Pro** 是一款面向企业的智能硬件性能监控与资产管理平台，支持 **5万台设备** 的企业级部署。

- **集中管理** - 集中监控公司所有开发设备的硬件信息
- **实时监控** - CPU/GPU/内存/磁盘/网络实时监控
- **智能分析** - AI驱动的硬件性能分析与岗位匹配
- **远程控制** - 远程关机、重启、唤醒等控制功能
- **权限管理** - RBAC角色权限管理
- **数据驱动** - 识别性能瓶颈，提供升级建议

---

## 技术栈

### 后端
- Python 3.10+ / FastAPI
- SQLAlchemy (ORM)
- PostgreSQL + TimescaleDB (支持5万台设备)
- SQLite (轻量级部署可选)

### 前端
- Vue 3 + TypeScript
- Vite 构建
- Naive UI 组件库
- ECharts 数据可视化
- Pinia 状态管理
- **Inspira UI** 动画组件库
- **Tailwind CSS** 样式框架
- **Marked** Markdown 渲染
- **Shadcn Vue** UI 组件

### Agent (Windows 客户端)
- **Node.js** - 使用 [systeminformation](https://github.com/sebhildebrandt/systeminformation) 库进行硬件信息采集
- **Python** - 客户端核心逻辑
- **NVIDIA nvidia-smi** - GPU监控备选方案
- 自动注册和心跳
- 实时性能监控上报
- 远程控制命令执行

**为什么选择 systeminformation？**
- 19,000+ 行代码，700+ 版本发布
- 月下载量 2000万+，NPM 后端包排名前 10
- 完全支持 Windows/Linux/macOS
- 比 psutil + WMI 方案准确 10 倍以上

---

## 快速开始
### 服务端一键部署脚本（仅支持Windows，请在PowerShell内运行）

```bash
irm https://raw.githubusercontent.com/910610915/RoleFit-Pro/main/install-fresh.ps1 | iex
---

### 前置要求
- Python 3.10+
- Node.js 18+

### 运行后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化基础数据（首次运行）
python init_basic_data.py

# 启动服务
uvicorn app.main:app --reload
```

后端运行地址: http://localhost:8000

### 运行前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行地址: http://localhost:5173

### 部署 Agent (Windows 客户端)

```bash
cd agent

# 方式1: 一键部署 (推荐)
# 直接双击 deploy.bat，自动安装所有依赖并创建桌面快捷方式

# 方式2: 手动部署
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
cd nodejs/hardware_info
npm install
cd ../..

# 启动 Agent (双窗口模式)
# 方式1: 使用 launcher.bat (自动检测环境)
launcher.bat

# 方式2: 手动启动
python hardware_agent.py --server http://localhost:8000
python hardware_monitor.py
```

**Agent 功能说明：**
- `hardware_agent.py` - 设备注册、心跳、软件测试任务执行
- `hardware_monitor.py` - 实时硬件性能监控（CPU/GPU/内存/磁盘/网络/进程）
- 使用 **Node.js + systeminformation** 获取准确的硬件信息
- 使用 **nvidia-smi** 作为 GPU 监控备选方案
- 支持远程控制命令拉取和执行

---

## 项目结构

```
RoleFit Pro/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 核心配置
│   │   ├── models/       # 数据库模型
│   │   ├── schemas/      # Pydantic 模型
│   │   └── services/     # 业务逻辑
│   └── requirements.txt
├── frontend/              # Vue 前端
│   ├── src/
│   │   ├── api/         # API 客户端
│   │   ├── components/  # 组件
│   │   ├── views/       # 页面视图
│   │   └── router/      # 路由配置
│   └── package.json
├── agent/                # Windows Agent
│   ├── hardware_agent.py    # Agent 主程序
│   ├── hardware_monitor.py  # 实时监控
│   ├── nodejs_hardware.py  # Node.js 包装器
│   ├── nodejs/
│   │   └── hardware_info/  # Node.js 硬件采集
│   │       └── hardware_info.js
│   ├── blender_benchmark.py # Blender 测试
│   ├── maya_benchmark.py    # Maya 测试
│   ├── unreal_benchmark.py  # Unreal 测试
│   ├── command_executor.py  # 命令执行器
│   └── software_manager.py  # 软件管理
├── docs/
│   └── plans/              # 设计文档
│       ├── 2026-03-08-rolefit-pro-enterprise-design.md
│       └── 2026-03-08-rolefit-pro-development-plan.md
└── README.md
```

---

## 核心功能

### 1. 设备管理
- 设备注册 (Agent 自动注册 / 手动添加)
- 硬件信息展示 (CPU/GPU/内存/磁盘)
- 设备状态监控 (在线/离线/测试中)
- 设备分组 (按部门/岗位)
- **设备画像** - 完整的设备档案（归属信息、采购信息、使用统计）

### 2. 实时性能监控
- CPU 监控（利用率、频率、温度）
- GPU 监控（利用率、显存、温度，支持 NVIDIA nvidia-smi）
- 内存监控（使用率、已用/可用）
- 磁盘IO监控（读取/写入速度）
- 网络监控（上传/下载速度）
- **进程监控** - Top 10 资源消耗进程

### 3. 趋势分析
- CPU 趋势图（1分钟/5分钟/15分钟）
- GPU 趋势图
- 内存趋势图
- 磁盘IO趋势图

### 4. 智能告警
- 自定义告警规则
- CPU/GPU 高温告警
- 内存/磁盘空间不足告警
- 硬盘寿命告警（SMART监控）
- 设备离线告警

### 5. 远程控制
- 远程关机/重启
- 远程锁定
- 远程唤醒 (Wake-on-LAN)
- 远程命令执行

### 6. 权限管理 (RBAC)
- 角色管理（超级管理员、IT管理员、运维人员、部门管理员、只读用户）
- 权限细粒度控制
- 部门数据隔离
- 审计日志

### 7. 第三方集成
- 资产管理平台 API 对接
- 企业通讯工具集成
- 可配置的 API 网关

### 8. 岗位管理
- 预设岗位配置 (程序、美术、TA、VFX、视频)
- 自定义岗位需求
- 岗位标准设置

### 9. 软件管理
- 测试软件库 (VS、UE、Maya、Blender、PS、PR、AE 等)
- 自动安装/检测
- 软件版本管理

### 10. 脚本管理
- 40+ 岗位测试脚本
- 自动化执行 (编译、渲染、视口测试)
- 性能指标采集

### 11. 任务系统
- 创建测试任务
- 定时任务调度
- 执行状态跟踪
- 任务历史记录

### 12. 数据分析
- 性能趋势分析
- 瓶颈识别
- 达标判定
- 升级建议

### 13. AI 智能分析
- LLM 驱动的硬件性能分析
- 多 AI 提供商支持 (MiniMax、DeepSeek、智谱等)
- 自动化瓶颈诊断
- 升级建议生成

### 14. AI 智能对话助手
- 侧边栏式 AI 对话（类似 Chrome 插件体验）
- 支持查询设备列表、状态、性能等
- Markdown 表格格式展示
- 支持多 LLM 提供商

### 15. Inspira UI 动画特效
- Spotlight 卡片效果
- Glare 卡片效果
- 数字滚动动画
- 列表渐入动画
- 闪烁粒子背景
- 渐变边框光效
- 彩带庆祝动画

### 16. 数据保留策略
- 可配置的数据保留天数（3/7/14/30/90天）
- 自动清理过期数据
- 可配置的采集间隔（1/5/10/30/60秒）

---

## 前端组件使用

### Inspira UI 组件

```vue
<script setup>
import { 
  InspiraButton, 
  InspiraCard, 
  InspiraSparkles,
  InspiraNumberTicker,
  InspiraBorderBeam,
  InspiraConfetti,
  InspiraBentoGrid,
  InspiraAnimatedList,
  RainbowButton
} from '@/components/inspira'
</script>

<template>
  <!-- 动画按钮 -->
  <InspiraButton variant="shimmer">Shimmer 按钮</InspiraButton>
  <InspiraButton variant="gradient">渐变按钮</InspiraButton>
  <InspiraButton variant="rainbow">彩虹按钮</InspiraButton>
  <RainbowButton>彩虹按钮</RainbowButton>
  
  <!-- 卡片 -->
  <InspiraCard variant="spotlight">Spotlight 卡片</InspiraCard>
  <InspiraCard variant="glare">Glare 卡片</InspiraCard>
  
  <!-- 背景 -->
  <InspiraSparkles :density="100">
    内容...
  </InspiraSparkles>
  
  <!-- 数字滚动 -->
  <InspiraNumberTicker :value="1234" suffix="台" />
  
  <!-- 边框光效 -->
  <InspiraBorderBeam>内容</InspiraBorderBeam>
  
  <!-- 彩带 -->
  <InspiraConfetti :show="showConfetti" />
  
  <!-- 网格布局 -->
  <InspiraBentoGrid :cols="3" gap="lg">
    <InspiraCard>卡片1</InspiraCard>
    <InspiraCard>卡片2</InspiraCard>
    <InspiraCard>卡片3</InspiraCard>
  </InspiraBentoGrid>
  
  <!-- 列表动画 -->
  <InspiraAnimatedList variant="stagger">
    <li>项目1</li>
    <li>项目2</li>
    <li>项目3</li>
  </InspiraAnimatedList>
</template>
```

### Shadcn Vue 组件

```vue
<script setup>
import SleekLineCursor from '@/components/ui/sleek-line-cursor/SleekLineCursor.vue'
import AuroraBackground from '@/components/ui/aurora-background/AuroraBackground.vue'
</script>

<template>
  <!-- 极光背景 -->
  <AuroraBackground>
    页面内容
  </AuroraBackground>
  
  <!-- 鼠标光标轨迹 -->
  <SleekLineCursor :trails="20" :size="50" />
</template>
```

---

## 特效展示

## 支持的软件

| 岗位 | 软件 |
|------|------|
| 程序开发 | Visual Studio, Unreal Engine, Unity |
| 美术设计 | Photoshop, Illustrator, Maya, Blender, ZBrush |
| 动画制作 | Maya, Blender, C4D |
| VFX | After Effects, Nuke, Houdini |
| 视频制作 | Premiere Pro, DaVinci Resolve |
| UI 设计 | Figma, Sketch, Adobe XD |

---

## API 文档

访问 http://localhost:8000/docs 查看完整 API 文档

主要端点：
- POST /api/auth/login - 用户登录
- GET /api/devices - 设备列表
- GET /api/devices/search - 设备搜索
- GET /api/devices/{id}/profile - 设备画像
- POST /api/devices/agent/register - Agent 注册
- POST /api/devices/{id}/control - 远程控制命令
- GET /api/software - 软件列表
- GET /api/scripts - 测试脚本
- POST /api/tasks - 创建任务
- GET /api/results - 测试结果
- GET /api/stats/dashboard - 仪表盘统计
- GET /api/performance/metrics - 性能指标
- GET /api/performance/metrics/trend - 趋势数据
- GET /api/performance/processes - 进程列表
- GET /api/performance/alerts - 告警列表
- POST /api/ai_analysis/analyze - AI 分析
- GET /api/scheduler/status - 调度器状态
- GET /api/audit-logs - 审计日志
- GET /api/roles - 角色列表
- GET /api/third-party-apis - 第三方API配置

---

## 环境配置

### 后端 (.env)

```env
APP_NAME=RoleFit Pro
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./hardware_benchmark.db
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=["*"]

# LLM 配置
LLM_PROVIDER=nvidia  # siliconflow/minimax/deepseek/zhipu/qwen/openai/nvidia
LLM_API_KEY=your_api_key
LLM_MODEL=meta/llama-3.1-8b-instruct
```

### 前端 (.env)

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 默认账号

- 用户名: admin
- 密码: admin123

请及时修改默认密码！

---

## 许可证

MIT License

---

© 2024 RoleFit Pro. All rights reserved.

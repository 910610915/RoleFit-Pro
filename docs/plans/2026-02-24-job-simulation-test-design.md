# 岗位模拟测试系统 - 技术设计文档

## 1. 项目概述

### 1.1 目标

在现有硬件性能基准测试系统的基础上，新增**岗位模拟测试功能**，通过自动化脚本模拟员工真实工作场景，采集软件运行指标，为IT部门提供精准的岗位电脑选型和升级依据。

### 1.2 核心价值

- **贴近真实**：模拟实际工作操作，而非抽象的硬件跑分
- **岗位定向**：按不同岗位配置测试脚本，评估岗位匹配度
- **自动化**：全流程自动化执行，无需人工干预
- **可量化**：采集多维度指标，生成量化报告

---

## 2. 系统架构

### 2.1 整体架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Web管理平台 (现有)                             │
│   设备管理 | 任务管理 | 结果分析 | 岗位标准 | 系统设置              │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ 基准测试模块   │    │ 岗位模拟模块   │    │ 公共模块      │
│ (现有功能)     │    │ (新增功能)     │    │ (用户/设备)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                       │
        │               ┌───────┴───────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Benchmark     │  │ Job Sim       │  │ Data         │
│ Agent         │  │ Agent         │  │ Collection    │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 2.2 技术架构

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端 | FastAPI + SQLAlchemy | 现有架构，扩展API |
| 前端 | Vue3 + Naive UI | 现有架构，新增页面 |
| Agent | Python + PyAutoGUI + psutil | Windows自动化 |
| 数据库 | SQLite | 现有架构，扩展表 |

---

## 3. 数据模型设计

### 3.1 新增表结构

```python
# 3.1.1 岗位配置表 (Position)
Position:
  - id: UUID (PK)
  - position_name: str (岗位名称, 如"UE开发")
  - position_code: str (岗位代码, 如"UE_DEV")
  - department: str (部门)
  - description: str
  - is_active: bool
  - created_at: datetime
  - updated_at: datetime

# 3.1.2 测试软件表 (TestSoftware)
TestSoftware:
  - id: UUID (PK)
  - software_name: str (软件名称, 如"Unreal Engine 5")
  - software_code: str (软件代码, 如"UE5")
  - vendor: str (厂商, 如"Epic Games")
  - category: str (分类: DEV/ART/ANIM/VFX/TOOL/OFFICE)
  - install_path: str (安装路径)
  - launch_params: str (启动参数)
  - is_active: bool
  - created_at: datetime

# 3.1.3 测试脚本表 (JobScript)
JobScript:
  - id: UUID (PK)
  - script_name: str (脚本名称, 如"UE5项目启动测试")
  - script_code: str (脚本代码, 如"UE5_PROJECT_START")
  - position_id: UUID (FK -> Position)
  - software_id: UUID (FK -> TestSoftware)
  - script_type: str (START/OPERATION/RENDER/STRESS)
  - script_content: JSON (自动化脚本内容)
  - expected_duration: int (秒)
  - is_active: bool
  - created_at: datetime

# 3.1.4 脚本执行记录表 (ScriptExecution)
ScriptExecution:
  - id: UUID (PK)
  - task_id: UUID (FK -> TestTask)
  - script_id: UUID (FK -> JobScript)
  - device_id: UUID (FK -> Device)
  - start_time: datetime
  - end_time: datetime
  - duration_seconds: int
  - exit_code: int (0=成功)
  - error_message: str
  - created_at: datetime

# 3.1.5 软件指标数据表 (SoftwareMetrics)
SoftwareMetrics:
  - id: UUID (PK)
  - execution_id: UUID (FK -> ScriptExecution)
  - timestamp: datetime
  - software_name: str
  - process_id: int
  - cpu_percent: float
  - memory_mb: float
  - gpu_percent: float
  - gpu_memory_mb: float
  - disk_read_mbps: float
  - disk_write_mbps: float
  - fps: float (帧率, 如游戏引擎)
  - latency_ms: float (响应延迟)
  - status: str (RUNNING/IDLE/CRASHED)
  - created_at: datetime
```

### 3.2 扩展现有表

```python
# 扩展 TestTask 表
TestTask:
  + task_category: str (BENCHMARK / JOB_SIMULATION)
  + position_id: UUID (FK -> Position)  # 岗位模拟专用

# 扩展 TestResult 表
TestResult:
  + task_category: str
  + position_id: UUID
  + software_metrics: JSON (软件指标汇总)
  + performance_score: float (岗位综合评分)
  + recommendation: str (选型建议)
```

---

## 4. API设计

### 4.1 岗位管理API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/positions | 岗位列表 |
| POST | /api/positions | 创建岗位 |
| GET | /api/positions/{id} | 岗位详情 |
| PUT | /api/positions/{id} | 更新岗位 |
| DELETE | /api/positions/{id} | 删除岗位 |

### 4.2 测试软件API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/software | 软件列表(支持分类筛选) |
| POST | /api/software | 添加软件 |
| GET | /api/software/{id} | 软件详情 |
| PUT | /api/software/{id} | 更新软件 |
| DELETE | /api/software/{id} | 删除软件 |

### 4.3 测试脚本API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/scripts | 脚本列表 |
| POST | /api/scripts | 创建脚本 |
| GET | /api/scripts/{id} | 脚本详情 |
| PUT | /api/scripts/{id} | 更新脚本 |
| DELETE | /api/scripts/{id} | 删除脚本 |
| POST | /api/scripts/{id}/test | 测试运行脚本 |

### 4.4 执行结果API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/executions | 执行记录列表 |
| GET | /api/executions/{id} | 执行详情(含实时指标) |
| GET | /api/executions/{id}/metrics | 指标时序数据 |
| GET | /api/results/analysis/{device_id} | 设备岗位匹配度分析 |

---

## 5. Agent设计

### 5.1 自动化脚本引擎

```python
class ScriptEngine:
    """自动化脚本执行引擎"""
    
    def execute(self, script: JobScript, device: Device) -> ScriptExecution:
        """执行单个脚本"""
        # 1. 启动目标软件
        # 2. 执行预设操作
        # 3. 采集运行指标
        # 4. 记录执行结果
        
    def collect_metrics(self, software_name: str) -> SoftwareMetrics:
        """采集软件运行指标"""
        # 使用 psutil 采集CPU/内存/磁盘
        # 使用 pywinauto 采集窗口信息
        # 使用 NVIDIA/AMD API 采集GPU指标
```

### 5.2 脚本操作类型

| 类型 | 示例 | 采集重点 |
|------|------|----------|
| START | 启动软件、打开项目 | 启动耗时、初始内存 |
| OPERATION | 切换场景、编译代码 | 操作延迟、响应时间 |
| RENDER | 烘焙、导出 | 渲染耗时、GPU占用 |
| STRESS | 多软件同时运行 | 资源争用、帧率下降 |

### 5.3 脚本定义示例

```json
{
  "script_code": "UE5_PROJECT_START",
  "script_type": "START",
  "operations": [
    {
      "action": "launch",
      "software": "UnrealEditor.exe",
      "params": ["E:\\Projects\\MyGame\\MyGame.uproject"],
      "wait_for": "EditorLoaded"
    },
    {
      "action": "wait",
      "duration": 30
    },
    {
      "action": "capture",
      "name": "initial_load"
    },
    {
      "action": "close"
    }
  ],
  "metrics": [
    "cpu", "memory", "gpu", "gpu_memory", "disk"
  ]
}
```

---

## 6. 前端页面设计

### 6.1 新增页面

| 页面 | 路由 | 说明 |
|------|------|------|
| 岗位管理 | /positions | 岗位列表、新增、编辑 |
| 软件管理 | /software | 测试软件库、分类浏览 |
| 脚本管理 | /scripts | 测试脚本库、脚本编辑器 |
| 岗位分析 | /analysis | 岗位匹配度、设备分析 |

### 6.2 页面布局

#### 6.2.1 岗位管理页面
```
┌─────────────────────────────────────────────────────┐
│  岗位管理                              [+新增岗位] │
├─────────────────────────────────────────────────────┤
│ 筛选: [全部部门 ▼] [全部岗位 ▼] [搜索...]          │
├─────────────────────────────────────────────────────┤
│ 岗位名称    │ 部门   │ 软件数量 │ 创建时间 │ 操作 │
│ UE开发      │ 技术部 │ 8        │ 2024-01  │ ✏️ 🗑 │
│ Unity开发   │ 技术部 │ 6        │ 2024-01  │ ✏️ 🗑 │
│ 3D美术      │ 美术部 │ 12       │ 2024-01  │ ✏️ 🗑 │
└─────────────────────────────────────────────────────┘
```

#### 6.2.2 软件管理页面
```
┌─────────────────────────────────────────────────────┐
│  测试软件                                    [+添加软件] │
├─────────────────────────────────────────────────────┤
│ 分类: [全部] [开发] [美术] [动画] [特效] [工具] [办公] │
├─────────────────────────────────────────────────────┤
│ ┌─────────┐  Unreal Engine 5    Epic Games    开发 │
│ │   UE5   │  版本: 5.4.2         安装路径: C:\...   │
│ └─────────┘  脚本数: 5           [编辑] [查看脚本]   │
│ ┌─────────┐  Unity 2023          Unity Tech      开发 │
│ │  Unity  │  版本: 2023.2.0      安装路径: C:\...   │
│ └─────────┘  脚本数: 4           [编辑] [查看脚本]   │
└─────────────────────────────────────────────────────┘
```

#### 6.2.3 脚本管理页面
```
┌─────────────────────────────────────────────────────┐
│  测试脚本                          [+新建脚本]      │
├─────────────────────────────────────────────────────┤
│ 脚本名称          │ 所属岗位 │ 软件    │ 类型  │ 操作 │
│ UE5项目启动       │ UE开发   │ UE5     │ START │ ▶️ ▶️ ✏️ │
│ UE5蓝图编译       │ UE开发   │ UE5     │ OP    │ ▶️ ▶️ ✏️ │
│ Maya场景渲染      │ 3D美术   │ Maya    │ RENDER│ ▶️ ▶️ ✏️ │
│ PS大文件处理      │ UI设计   │ PS      │ OP    │ ▶️ ▶️ ✏️ │
└─────────────────────────────────────────────────────┘
```

#### 6.2.4 岗位分析页面
```
┌─────────────────────────────────────────────────────┐
│  岗位匹配度分析                                                 │
├─────────────────────────────────────────────────────┤
│ 设备: [Dev-PC-001 ▼]  岗位: [UE开发 ▼]  [开始分析]          │
├─────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐ │
│ │                    分析报告                     │ │
│ │  匹配度: ████████████░░░░░░  75%              │ │
│ │                                                  │ │
│ │  软件启动测试                                    │ │
│ │  ├─ Unreal Engine: 28秒 (标准: 30秒) ✅        │ │
│ │  ├─ Visual Studio: 15秒 (标准: 20秒) ✅       │ │
│ │  └─ Rider: 12秒 (标准: 15秒) ✅               │ │
│ │                                                  │ │
│ │  资源占用                                       │ │
│ │  ├─ CPU平均: 65% (峰值: 89%)                  │ │
│ │  ├─ 内存: 24GB/32GB (75%)                    │ │
│ │  └─ GPU: 72% (显存: 6GB/8GB)                  │ │
│ │                                                  │ │
│ │  建议: 建议升级内存至64GB，可提升编译效率       │ │
│ └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 7. 与现有功能的整合

### 7.1 任务类型扩展

现有任务系统扩展`task_category`字段：

| task_category | 说明 | 创建方式 |
|---------------|------|----------|
| BENCHMARK | 硬件基准测试 | 现有功能 |
| JOB_SIMULATION | 岗位模拟测试 | 新增功能 |

### 7.2 任务创建流程

```
创建任务
    │
    ├─ 选择任务类型
    │   ├─ 基准测试 → 现有流程
    │   └─ 岗位模拟 → 新流程
    │       │
    │       ├─ 1. 选择岗位
    │       ├─ 2. 选择测试脚本(可选预置套餐)
    │       ├─ 3. 选择目标设备
    │       └─ 4. 设置调度
    │
    └─ 任务执行
        ├─ 基准测试 → 现有Agent
        └─ 岗位模拟 → 新Job Agent
```

### 7.3 结果展示整合

测试结果详情页增加`task_category`判断：

- `BENCHMARK`: 显示现有基准测试结果(分数、排名)
- `JOB_SIMULATION`: 显示新的岗位分析结果(软件指标、匹配度)

---

## 8. 实现计划

### 8.1 Phase 1: 基础架构

1. 创建数据库表(Position, TestSoftware, JobScript, ScriptExecution, SoftwareMetrics)
2. 实现基础CRUD API
3. 开发前端基础页面

### 8.2 Phase 2: 脚本引擎

1. 实现ScriptEngine自动化执行框架
2. 开发常见软件的操作库(UE/Unity/PS/Maya等)
3. 实现指标采集模块

### 8.3 Phase 3: 集成测试

1. 岗位配置管理(预设岗位+软件)
2. 完整任务流程测试
3. 结果分析与报告

### 8.4 Phase 4: 优化

1. 脚本模板优化
2. 性能优化
3. 用户体验完善

---

## 9. 风险与约束

### 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 软件版本兼容性 | 脚本可能失效 | 版本检测+适配 |
| 自动化不稳定 | 测试结果波动 | 多次取平均 |
| 资源采集延迟 | 指标不准确 | 高频采样+滤波 |

### 9.2 约束

- 仅支持Windows平台(主流开发环境)
- 需要目标软件已安装(不支持自动安装)
- 部分软件需要license

---

## 10. 验收标准

### 10.1 功能验收

- [ ] 可创建/编辑/删除岗位
- [ ] 可管理测试软件库
- [ ] 可创建/编辑/测试自动化脚本
- [ ] 可创建岗位模拟任务并执行
- [ ] 可查看执行结果和软件指标
- [ ] 可生成岗位匹配度分析报告

### 10.2 性能验收

- [ ] 单脚本执行响应 < 100ms
- [ ] 指标采集频率 >= 1Hz
- [ ] 100并发任务执行稳定

### 10.3 体验验收

- [ ] 页面加载 < 2s
- [ ] 操作响应 < 500ms
- [ ] 图表渲染流畅

---

*文档版本: 1.0*  
*创建日期: 2026-02-24*  
*作者: Sisyphus AI*

# RoleFit Pro AI 自动化功能设计方案

## 一、系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           服务端 (Backend)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │  数据采集API  │  │  控制命令API  │  │  可视化API   │  │ AI分析API │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └───────────┘ │
│         │                 │                 │                │         │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │                     SQLite 数据库                            │     │
│  │  devices | metrics | alerts | positions | job_requirements  │     │
│  └──────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
         ↑                         ↑                      ↑
    心跳/上报                 控制命令              AI分析请求
         │                         │                      │
┌────────┴────────┐      ┌────────┴────────┐     ┌────────┴────────┐
│   Agent 1      │      │   Agent 2      │     │   Agent N      │
│ (员工电脑A)    │      │ (员工电脑B)    │     │ (员工电脑N)    │
│ ┌───────────┐  │      │ ┌───────────┐  │     │ ┌───────────┐  │
│ │硬件采集   │  │      │ │硬件采集   │  │     │ │硬件采集   │  │
│ │性能测试   │  │      │ │性能测试   │  │     │ │性能测试   │  │
│ │软件控制   │  │      │ │软件控制   │  │     │ │软件控制   │  │
│ └───────────┘  │      │ └───────────┘  │     │ └───────────┘  │
└───────────────┘      └───────────────┘     └───────────────┘
```

## 二、核心功能模块

### 2.1 数据采集层 (Data Collection)

#### 采集指标分类

| 类别 | 指标 | 采集方式 | 频率 |
|------|------|----------|------|
| **硬件基础** | CPU型号/核心数/频率 | WMI | 每天 |
| | GPU型号/VRAM | WMI | 每天 |
| | 内存总量/使用率 | psutil | 实时 |
| | 磁盘类型/容量 | WMI | 每天 |
| **性能测试** | 软件启动时间 | subprocess + 计时 | 按需 |
| | 编译速度 (VS/UE) | 实际编译测试 | 按需 |
| | 渲染时间 (Blender/Maya) | 渲染测试 | 按需 |
| | FPS (游戏/实时预览) | 内置测试 | 按需 |
| **软件状态** | 已安装软件列表 | 注册表 | 每天 |
| | 正在运行的软件 | psutil | 5分钟 |
| | GPU利用率 | nvidia-smi / WMI | 实时 |
| **温度与功耗** | CPU/GPU温度 | WMI/OpenHardwareMonitor | 实时 |
| | 功耗 | WMI | 实时 |

#### 采集数据结构

```python
class PerformanceMetric:
    device_id: str          # 设备ID
    timestamp: datetime    # 采集时间
    
    # 硬件状态
    cpu_usage: float       # CPU使用率 %
    cpu_temp: float        # CPU温度
    gpu_usage: float       # GPU使用率 %
    gpu_temp: float        # GPU温度
    gpu_vram_used: int     # GPU显存使用 MB
    ram_usage: float       # 内存使用率 %
    
    # 性能测试结果 (如果有)
    software_tests: List[SoftwareTestResult]
    
    # 快照信息
    snapshot: Dict[str, Any]  # 完整硬件信息
```

### 2.2 控制层 (Control Layer)

#### 控制命令类型

| 命令 | 说明 | 参数 | 示例 |
|------|------|------|------|
| `launch_software` | 启动软件 | software_name, path | 启动 Photoshop |
| `close_software` | 关闭软件 | process_name | 关闭 Photoshop |
| `run_benchmark` | 运行基准测试 | benchmark_type, software | 测试 UE5 编译 |
| `capture_screenshot` | 截屏 | - | - |
| `get_metrics` | 获取实时指标 | - | - |
| `install_software` | 安装软件 | software_name, installer_path | - |

#### 控制命令API

```python
# POST /api/agent/command
{
    "device_id": "xxx",
    "command": "launch_software",
    "params": {
        "software": "Photoshop",
        "path": "C:\\Program Files\\Adobe\\..."
    }
}

# Response
{
    "task_id": "uuid",
    "status": "pending" | "running" | "completed" | "failed",
    "result": {}
}
```

### 2.3 可视化层 (Visualization)

#### 页面设计

**1. 监控大屏 (Dashboard)**
- 实时显示所有在线设备
- 整体健康状态 (达标/警告/不达标)
- 按部门分组的设备列表
- 告警信息流

**2. 设备详情页**
- 实时硬件指标 (CPU/GPU/内存)
- 性能历史趋势图
- 已安装软件列表
- 岗位匹配度

**3. 性能分析页**
- 软件性能对比
- 部门/岗位性能排名
- 瓶颈分析

**4. 告警中心**
- 性能告警
- 离线告警
- 岗位不匹配告警

### 2.4 AI 分析层 (AI Analysis)

#### 岗位需求定义

```python
class JobRequirement:
    id: str
    name: str              # "游戏开发工程师"
    department: str        # "研发部"
    
    # 最低要求
    min_cpu_cores: int
    min_cpu_ghz: float
    min_ram_gb: int
    min_gpu_vram_gb: int
    min_gpu_model: str     # "RTX 3060" or better
    
    # 推荐配置
    recommended_cpu: str
    recommended_gpu: str
    recommended_ram_gb: int
    
    # 测试要求
    required_software: List[str]  # 必须安装的软件
    max_startup_time: Dict[str, int]  # {"Photoshop": 10} 秒
    min_fps: Dict[str, float]      # {"UnrealEditor": 30}
```

#### AI 分析功能

1. **自动评估**
   - 对比硬件与岗位需求
   - 计算匹配度百分比
   - 识别瓶颈组件

2. **升级建议**
   - 基于当前硬件推荐升级方案
   - 估算性能提升
   - 成本估算

3. **智能报告**
   - 生成设备健康报告
   - 部门性能总结
   - 投资建议

## 三、数据库设计

### 新增表

```sql
-- 性能指标记录
CREATE TABLE performance_metrics (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 基础指标
    cpu_usage FLOAT,
    cpu_temp FLOAT,
    gpu_usage FLOAT,
    gpu_temp FLOAT,
    gpu_vram_used INT,
    ram_usage FLOAT,
    ram_total_gb FLOAT,
    
    -- 磁盘
    disk_read_speed INT,
    disk_write_speed INT,
    
    -- 网络
    network_upload_speed INT,
    network_download_speed INT,
    
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- 软件性能测试结果
CREATE TABLE software_benchmarks (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    software_name VARCHAR(100) NOT NULL,
    
    startup_time FLOAT,      -- 启动时间(秒)
    memory_usage_mb INT,    -- 内存使用
    cpu_usage FLOAT,         -- CPU使用率
    gpu_usage FLOAT,          -- GPU使用率
    
    test_result JSON,        -- 详细测试结果
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- 岗位需求配置
CREATE TABLE job_requirements (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    description TEXT,
    
    -- 最低配置
    min_cpu_cores INT DEFAULT 4,
    min_cpu_ghz FLOAT DEFAULT 2.0,
    min_ram_gb INT DEFAULT 16,
    min_gpu_vram_gb INT DEFAULT 4,
    min_gpu_model VARCHAR(100),
    
    -- 推荐配置
    recommended_cpu VARCHAR(200),
    recommended_gpu VARCHAR(200),
    recommended_ram_gb INT DEFAULT 32,
    
    -- 测试要求 (JSON)
    software_requirements JSON,
    max_startup_times JSON,
    min_fps JSON,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 设备岗位匹配记录
CREATE TABLE device_job_matching (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    job_requirement_id VARCHAR(36) NOT NULL,
    
    match_score FLOAT,       -- 匹配度 0-100
    is_recommended BOOLEAN,  -- 是否推荐该岗位
    
    cpu_match BOOLEAN,
    gpu_match BOOLEAN,
    ram_match BOOLEAN,
    
    bottleneck TEXT,         -- 瓶颈描述
    upgrade_suggestions JSON, -- 升级建议
    
    analyzed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(id),
    FOREIGN KEY (job_requirement_id) REFERENCES job_requirements(id)
);

-- 控制命令记录
CREATE TABLE control_commands (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    
    command VARCHAR(50) NOT NULL,
    params JSON,
    
    status VARCHAR(20) DEFAULT 'pending',  -- pending/running/completed/failed
    result JSON,
    
    issued_by VARCHAR(36),    -- 下发人
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- 告警记录
CREATE TABLE performance_alerts (
    id VARCHAR(36) PRIMARY KEY,
    device_id VARCHAR(36) NOT NULL,
    
    alert_type VARCHAR(50),   -- offline/high_temp/low_performance/job_mismatch
    severity VARCHAR(20),      -- info/warning/error/critical
    
    title VARCHAR(200),
    message TEXT,
    
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at DATETIME,
    resolved_by VARCHAR(36),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

## 四、API 设计

### 4.1 性能指标 API

```python
# GET /api/metrics/{device_id}
# 获取设备性能指标历史
{
    "device_id": "xxx",
    "metrics": [
        {
            "recorded_at": "2024-01-01T10:00:00",
            "cpu_usage": 45.2,
            "gpu_usage": 78.5,
            "ram_usage": 62.3,
            "gpu_temp": 65
        }
    ],
    "latest": { ... }
}

# GET /api/metrics/realtime/{device_id}
# 获取实时指标 (WebSocket 更佳)
```

### 4.2 岗位匹配 API

```python
# GET /api/positions/requirements
# 获取所有岗位需求

# POST /api/positions/requirements
# 创建岗位需求

# GET /api/devices/{device_id}/matching
# 获取设备与岗位的匹配情况
{
    "device_id": "xxx",
    "matches": [
        {
            "job_name": "游戏开发工程师",
            "match_score": 85.5,
            "cpu_match": True,
            "gpu_match": True,
            "ram_match": False,
            "bottleneck": "内存不足，建议升级到32GB",
            "upgrade_cost": "约2000元"
        }
    ]
}

# POST /api/ai/analyze
# AI 深度分析
{
    "device_id": "xxx",
    "analysis_type": "full" | "bottleneck" | "upgrade"
}
```

### 4.3 控制命令 API

```python
# POST /api/agent/command
# 下发控制命令
{
    "device_id": "xxx",
    "command": "run_benchmark",
    "params": {
        "software": "Photoshop",
        "test_type": "startup"
    }
}

# GET /api/agent/command/{task_id}
# 查询命令执行状态
```

### 4.4 告警 API

```python
# GET /api/alerts
# 获取告警列表

# POST /api/alerts/{id}/resolve
# 标记告警已处理
```

## 五、前端页面设计

### 5.1 新增页面

| 页面 | 路由 | 功能 |
|------|------|------|
| 监控大屏 | /dashboard | 实时监控所有设备 |
| 设备详情 | /devices/:id | 单设备详细信息 |
| 岗位管理 | /jobs | 岗位需求配置 |
| 性能分析 | /analysis | AI 分析报告 |
| 告警中心 | /alerts | 告警管理 |

### 5.2 现有页面增强

- **首页** - 添加监控大屏入口
- **设备管理** - 添加"立即测试"按钮
- **岗位管理** - 添加AI分析按钮

## 六、实施计划

### Phase 1: 基础设施 (1周)
1. 创建数据库表
2. 实现指标采集API
3. 实现设备详情API

### Phase 2: Agent 增强 (1周)
1. 添加实时指标采集
2. 添加软件启动时间测试
3. 添加控制命令接收

### Phase 3: 可视化 (1周)
1. 开发监控大屏
2. 开发设备详情页
3. 集成 ECharts 图表

### Phase 4: AI 集成 (1周)
1. 完善岗位需求模型
2. 实现匹配度计算
3. 集成 LLM 分析

### Phase 5: 优化 (0.5周)
1. 性能优化
2. 告警优化
3. 用户体验优化

## 七、关键技术点

### 7.1 实时通信
- 使用 WebSocket 进行实时指标推送
- Agent 心跳保持连接

### 7.2 安全考虑
- Agent 认证 (API Key)
- 命令授权 (只有管理员可下发)
- 敏感操作审计

### 7.3 性能考虑
- 指标数据分区存储 (按月)
- 定期清理历史数据
- 使用缓存减少数据库查询

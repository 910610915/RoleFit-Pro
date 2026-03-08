# RoleFit Pro 功能设计文档

**版本**: 2.0  
**日期**: 2026-03-08  
**状态**: 草稿

---

## 一、项目概述

### 1.1 项目背景

RoleFit Pro 是一款面向游戏开发公司的智能硬件性能基准测试与岗位匹配平台。随着公司规模扩大，需要支持 **5万台设备** 的企业级监控管理。

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + Naive UI)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 仪表盘  │ │设备管理 │ │性能监控 │ │ AI分析  │ │系统管理 │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/WebSocket
┌───────────────────────────▼─────────────────────────────────────┐
│                      后端 (FastAPI + PostgreSQL)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │  REST API   │ │ WebSocket   │ │  定时任务   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Agent (Windows 客户端)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │硬件信息采集 │ │性能监控上报 │ │ 远程控制    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue 3 + TypeScript | 组件化开发 |
| UI库 | Naive UI + Inspira UI | 企业级组件 + 动画特效 |
| 图表 | ECharts | 数据可视化 |
| 后端 | FastAPI | 异步高性能 |
| 数据库 | PostgreSQL + TimescaleDB | 时序数据专用 |
| Agent | Python + Node.js | 硬件信息采集 |

---

## 二、功能模块设计

### 2.1 性能监控模块

#### 2.1.1 实时监控

| 功能点 | 描述 |
|--------|------|
| CPU监控 | 利用率、频率、温度 |
| GPU监控 | 利用率、显存、温度（支持 NVIDIA nvidia-smi） |
| 内存监控 | 使用率、已用/可用 |
| 磁盘IO监控 | 读取/写入速度 |
| 网络监控 | 上传/下载速度 |

#### 2.1.2 趋势图表

| 图表类型 | 描述 |
|----------|------|
| CPU趋势图 | 实时折线图，支持1m/5m/15m时间范围 |
| GPU趋势图 | 实时折线图 |
| 内存趋势图 | 实时折线图 |
| 磁盘IO趋势图 | 实时折线图 |

#### 2.1.3 进程监控

| 功能点 | 描述 |
|--------|------|
| 进程列表 | 显示消耗资源最高的Top 10进程 |
| 进程信息 | 进程名、CPU%、内存、磁盘读写 |
| 用途 | 分析员工工作软件消耗情况 |

#### 2.1.4 性能告警

| 告警类型 | 触发条件 | 严重程度 |
|----------|----------|----------|
| CPU高温 | CPU > 90% 持续5分钟 | 🔴 严重 |
| GPU高温 | GPU > 85°C | 🟠 警告 |
| 内存不足 | 内存 > 90% | 🔴 严重 |
| 硬盘寿命不足 | SMART剩余寿命 < 10% | 🔴 严重 |
| 磁盘空间不足 | 任意分区 < 10GB | 🟠 警告 |
| 设备离线 | 超过5分钟无心跳 | 🟡 提醒 |

#### 2.1.5 数据保留策略

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| 数据保留天数 | 7天 | 可配置 3/7/14/30/90天 |
| 采集间隔 | 5秒 | 可配置 1/5/10/30/60秒 |
| 自动清理 | 每天凌晨3点 | 后台定时任务 |

---

### 2.2 设备管理模块

#### 2.2.1 新页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 搜索设备 [输入计算机名/IP/MAC搜索...]              [刷新]     │
├──────────────┬──────────────────────────────────────────────────────┤
│              │                                                       │
│  👤 设备信息  │   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  ──────────  │   │   CPU   │ │   GPU   │ │  内存   │ │  磁盘   │  │
│  名称: xxx   │   │    %    │ │    %    │ │    GB   │ │  MB/s   │  │
│  IP: xxx     │   └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│  MAC: xxx    │                                                       │
│  状态: 🟢    │   ┌──────────────────┐ ┌────────────────────────┐  │
│              │   │   CPU 趋势图     │ │   GPU 趋势图           │  │
│  💻 硬件信息 │   │   [ECharts]      │ │   [ECharts]           │  │
│  ──────────  │   └──────────────────┘ └────────────────────────┘  │
│  CPU: 5800X  │   ┌──────────────────┐ ┌────────────────────────┐  │
│  GPU: 5070   │   │  内存 趋势图     │ │   磁盘IO趋势图        │  │
│  内存: 32GB  │   │   [ECharts]      │ │   [ECharts]           │  │
│              │   └──────────────────┘ └────────────────────────┘  │
│  🚨 告警信息  │                                                       │
│  ──────────  │   ┌─────────────────────────────────────────────┐   │
│  ⚠️ CPU高温   │   │   进程资源消耗排行 (Top 10)                │   │
│              │   └─────────────────────────────────────────────┘   │
│              │                                                       │
│              │   ┌─────────────────────────────────────────────┐   │
│              │   │   🤖 AI 分析建议                           │   │
│              │   └─────────────────────────────────────────────┘   │
└──────────────┴──────────────────────────────────────────────────────┘
```

#### 2.2.2 设备搜索

| 功能点 | 描述 |
|--------|------|
| 搜索方式 | 支持按计算机名、IP、MAC地址搜索 |
| 模糊匹配 | 输入即搜索，防抖处理300ms |
| 分页展示 | 每次显示10条结果 |
| 搜索API | 后端提供 `/api/devices/search` 接口 |

#### 2.2.3 设备画像

| 维度 | 字段 |
|------|------|
| 基本信息 | 设备名称、IP、MAC、hostname、操作系统 |
| 硬件信息 | CPU型号/核数、GPU型号/显存、内存大小、磁盘信息 |
| 归属信息 | 所属部门、成本中心、使用人、岗位、工位位置 |
| 采购信息 | 采购日期、保修期、采购价格、供应商 |
| 使用信息 | 累计使用时长、最后使用时间、使用频率 |
| 故障历史 | 维修记录、故障类型、更换部件 |
| 软件信息 | 已安装软件列表、常用软件 |

---

### 2.3 远程控制模块

#### 2.3.1 控制功能

| 功能 | 技术方案 | 说明 |
|------|----------|------|
| 远程关机 | `shutdown /s /t 0` | 立即关机 |
| 远程重启 | `shutdown /r /t 0` | 立即重启 |
| 远程锁定 | `rundll32.exe user32.dll,LockWorkStation` | 锁定工作站 |
| 远程唤醒(WOL) | Magic Packet | 发送Wake-on-LAN包 |
| 远程执行命令 | WinRM/PyWinRM | 执行任意命令 |
| 远程桌面 | mstsc | 启动远程桌面连接 |

#### 2.3.2 消息队列

| 组件 | 说明 |
|------|------|
| 命令队列 | 服务器下发命令到队列 |
| Agent拉取 | Agent定时拉取待执行命令 |
| 结果回传 | 执行完成后回传结果 |
| 超时处理 | 命令超过5分钟未执行则取消 |

---

### 2.4 权限管理模块 (RBAC)

#### 2.4.1 角色设计

| 角色 | 权限范围 |
|------|---------|
| 超级管理员 | 全部权限，可管理所有用户和系统配置 |
| IT管理员 | 设备管理、监控、远程控制、工单处理 |
| 运维人员 | 监控查看、告警处理、远程协助 |
| 部门管理员 | 本部门设备管理 |
| 只读用户 | 仅查看监控数据 |

#### 2.4.2 权限粒度

| 权限项 | 说明 |
|--------|------|
| device:view | 查看设备列表和详情 |
| device:manage | 添加/编辑/删除设备 |
| device:control | 远程控制（关机/重启等） |
| monitor:view | 查看监控数据 |
| alert:view | 查看告警 |
| alert:handle | 处理告警 |
| user:manage | 用户管理 |
| system:config | 系统配置 |
| log:view | 查看审计日志 |

#### 2.4.3 数据模型

```
用户 (User)
  ├── id
  ├── username
  ├── email
  ├── role_id → 角色
  └── department_id → 部门

角色 (Role)
  ├── id
  ├── name
  ├── description
  └── permissions (JSON数组)

权限 (Permission)
  ├── id
  ├── code
  ├── name
  └── description
```

---

### 2.5 第三方集成模块

#### 2.5.1 配置管理

| 配置项 | 类型 | 说明 |
|--------|------|------|
| api_type | 下拉选择 | 资产管理平台/企业微信/钉钉/飞书 |
| api_url | 字符串 | API地址 |
| auth_type | 下拉选择 | API Key / Bearer Token / OAuth 2.0 / Basic Auth |
| api_key | 加密字符串 | 密钥 |
| extra_params | JSON | 额外参数 |
| enabled | 布尔值 | 是否启用 |
| last_test | 时间戳 | 最后测试时间 |
| test_status | 字符串 | success/failed |

#### 2.5.2 功能映射

| 第三方功能 | 集成方式 |
|------------|----------|
| 设备位置信息 | 调用API获取部门/位置信息 |
| 资产信息 | 同步设备归属/使用人 |
| 告警推送 | 机器人Webhook |
| 设备查询 | 自然语言处理后调用API |

---

### 2.6 审计日志模块

#### 2.6.1 记录内容

| 操作类型 | 记录内容 |
|----------|----------|
| 登录登出 | 用户、时间、IP、设备 |
| 设备操作 | 添加/修改/删除/远程控制 |
| 告警处理 | 告警内容、处理人、处理结果 |
| 配置变更 | 修改项、旧值、新值、管理员 |
| 数据导出 | 导出内容、导出人、时间 |

#### 2.6.2 日志字段

```python
class AuditLog:
    id: str
    user_id: str          # 操作人
    action: str           # 操作类型
    resource_type: str    # 资源类型
    resource_id: str      # 资源ID
    old_value: str        # 旧值
    new_value: str        # 新值
    ip_address: str       # IP地址
    user_agent: str       # 浏览器信息
    timestamp: datetime  # 操作时间
```

---

## 三、数据库设计

### 3.1 性能指标表 (performance_metrics)

```sql
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY,
    device_id UUID NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- CPU
    cpu_percent FLOAT,
    cpu_temperature FLOAT,
    cpu_frequency_mhz FLOAT,
    
    -- GPU
    gpu_percent FLOAT,
    gpu_temperature FLOAT,
    gpu_memory_used_mb FLOAT,
    gpu_memory_total_mb FLOAT,
    
    -- 内存
    memory_percent FLOAT,
    memory_used_mb FLOAT,
    memory_available_mb FLOAT,
    
    -- 磁盘
    disk_read_mbps FLOAT,
    disk_write_mbps FLOAT,
    
    -- 网络
    network_sent_mbps FLOAT,
    network_recv_mbps FLOAT,
    
    -- 进程
    process_count INTEGER,
    top_processes JSON,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- TimescaleDB 超表（5万台设备必备）
SELECT create_hypertable('performance_metrics', 'timestamp');
```

### 3.2 设备表 (devices) - 扩展

```sql
ALTER TABLE devices ADD COLUMN department_id VARCHAR(36);
ALTER TABLE devices ADD COLUMN cost_center VARCHAR(50);
ALTER TABLE devices ADD COLUMN assigned_user VARCHAR(100);
ALTER TABLE devices ADD COLUMN position VARCHAR(50);
ALTER TABLE devices ADD COLUMN location VARCHAR(200);
ALTER TABLE devices ADD COLUMN purchase_date DATE;
ALTER TABLE devices ADD COLUMN warranty_expiry DATE;
ALTER TABLE devices ADD COLUMN purchase_price DECIMAL(10,2);
ALTER TABLE devices ADD COLUMN supplier VARCHAR(200);
ALTER TABLE devices ADD COLUMN serial_number VARCHAR(100);
ALTER TABLE devices ADD COLUMN asset_tag VARCHAR(50);
```

### 3.3 审计日志表 (audit_logs)

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### 3.4 角色权限表

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSON,  -- ["device:view", "device:manage", ...]
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    department_id VARCHAR(36),  -- 部门隔离
    PRIMARY KEY (user_id, role_id)
);
```

---

## 四、API设计

### 4.1 设备搜索

```
GET /api/devices/search
  Query: q (搜索关键词)
  Query: department (部门筛选)
  Query: status (在线状态)
  Query: limit (默认10)
  Query: offset (分页)
  
Response: {
  "total": 100,
  "items": [
    {
      "id": "xxx",
      "device_name": "DESKTOP-ABC123",
      "ip_address": "192.168.1.100",
      "mac_address": "00-FF-CF-40-FB-8E",
      "status": "online",
      "cpu_model": "AMD Ryzen 7 5800X",
      "gpu_model": "NVIDIA GeForce RTX 5070",
      "last_seen_at": "2026-03-08T10:30:00"
    }
  ]
}
```

### 4.2 性能指标批量查询

```
GET /api/performance/metrics/batch
  Query: device_ids (逗号分隔的设备ID)
  Query: start_time
  Query: end_time
  Query: metrics (cpu,gpu,memory,disk)
  Query: interval (1m/5m/15m/1h)
  
Response: {
  "device_id": "xxx",
  "metrics": [
    {
      "timestamp": "2026-03-08T10:30:00",
      "cpu_percent": 45.5,
      "gpu_percent": 30.2,
      "memory_percent": 60.0
    }
  ]
}
```

### 4.3 远程控制命令

```
POST /api/devices/{device_id}/control
  Body: {
    "command": "shutdown|restart|lock|wol|exec",
    "params": {
      "timeout": 300,
      "command": "ipconfig"  // 仅exec类型需要
    }
  }
  
Response: {
  "command_id": "xxx",
  "status": "pending"
}

GET /api/devices/{device_id}/control/{command_id}
Response: {
  "command_id": "xxx",
  "status": "completed|failed|timeout",
  "result": "命令输出",
  "executed_at": "2026-03-08T10:30:00"
}
```

### 4.4 审计日志查询

```
GET /api/audit-logs
  Query: user_id
  Query: action
  Query: resource_type
  Query: start_time
  Query: end_time
  Query: limit
  
Response: {
  "total": 1000,
  "items": [...]
}
```

---

## 五、安全设计

### 5.1 认证

| 方式 | 说明 |
|------|------|
| 用户密码登录 | JWT Token |
| API Key认证 | 第三方系统接入 |
| Agent认证 | 设备注册时颁发Token |

### 5.2 授权

| 机制 | 说明 |
|------|------|
| RBAC | 基于角色的权限控制 |
| 部门隔离 | 部门管理员只能看本部门设备 |
| 操作审计 | 所有敏感操作记录日志 |

### 5.3 数据安全

| 措施 | 说明 |
|------|------|
| 密码加密 | bcrypt哈希存储 |
| API密钥加密 | AES加密存储 |
| HTTPS | 生产环境强制HTTPS |
| SQL注入防护 | ORM参数化查询 |

---

## 六、部署架构

### 6.1 单机部署（开发/小规模）

```
┌─────────────────────────────────────┐
│           应用服务器                 │
│  ┌─────────┐  ┌─────────┐          │
│  │ Frontend│  │ Backend │          │
│  └─────────┘  └─────────┘          │
│  ┌─────────────────────────────┐   │
│  │    PostgreSQL + TimescaleDB│   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 6.2 分布式部署（5万台）

```
┌──────────────────────────────────────────────────────────┐
│                        负载均衡                          │
└────────────────────────┬─────────────────────────────────┘
                         │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ Server 1│     │ Server 2│     │ Server N│
   │(API+WebS│     │(API+WebS│     │(API+WebS│
   └─────────┘     └─────────┘     └─────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
              ┌─────────────────┐
              │  PostgreSQL     │
              │  + TimescaleDB  │
              │  (主从复制)      │
              └─────────────────┘
```

### 6.3 服务器配置建议

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 16核32线程 | 32核64线程 |
| 内存 | 64GB | 128GB |
| 系统盘 | 500GB SSD | 1TB NVMe |
| 数据盘 | 2TB NVMe | 4TB NVMe RAID0 |
| 网络 | 1Gbps | 10Gbps |

---

## 七、版本规划

### Phase 1: 核心功能（紧急）

| 功能 | 优先级 | 预计工时 |
|------|--------|----------|
| GPU监控修复 | 🔴 P0 | 1天 |
| 内存/磁盘IO趋势图 | 🟠 P1 | 2天 |
| 进程监控看板 | 🟠 P1 | 3天 |
| 数据保留策略 | 🟠 P1 | 2天 |
| 新页面布局 | 🔴 P0 | 5天 |
| 设备搜索 | 🟠 P1 | 2天 |

### Phase 2: 运维功能

| 功能 | 优先级 | 预计工时 |
|------|--------|----------|
| 远程控制 | 🟠 P1 | 5天 |
| 增强告警 | 🟠 P1 | 3天 |
| 审计日志 | 🟡 P2 | 3天 |

### Phase 3: 权限与协作

| 功能 | 优先级 | 预计工时 |
|------|--------|----------|
| RBAC权限管理 | 🟠 P1 | 5天 |
| 设备画像 | 🟡 P2 | 5天 |

### Phase 4: 第三方集成

| 功能 | 优先级 | 预计工时 |
|------|--------|----------|
| 第三方API配置 | 🟡 P2 | 3天 |
| 分部地图集成 | 🟡 P2 | 3天 |
| 资产报表集成 | 🟡 P2 | 2天 |

---

## 八、附录

### 8.1 相关库依赖

**Agent端 (Python)**
- `systeminformation` - 硬件信息采集
- `pynvml` - NVIDIA GPU监控（可选）
- `pywakeonlan` - 远程唤醒
- `pywinrm` - 远程命令执行

**Agent端 (Node.js)**
- `systeminformation` - 硬件信息采集

**后端 (Python)**
- `fastapi` - Web框架
- `sqlalchemy` - ORM
- `psycopg2` - PostgreSQL驱动
- `timescaledb` - 时序数据库

### 8.2 参考文档

- [systeminformation文档](https://systeminformation.io/)
- [TimescaleDB文档](https://docs.timescale.com/)
- [NVIDIA NVML文档](https://docs.nvidia.com/deploy/nvml-api/)

---

**文档版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-03-08 | 初始版本 |

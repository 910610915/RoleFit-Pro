# RoleFit Pro 功能开发文档

**版本**: 2.0  
**日期**: 2026-03-08  
**状态**: 草稿

---

## 一、开发规范

### 1.1 代码规范

| 规范 | 说明 |
|------|------|
| 语言 | Python 3.10+ / TypeScript |
| 后端框架 | FastAPI |
| 前端框架 | Vue 3 + TypeScript |
| 数据库 | PostgreSQL + TimescaleDB |
| API风格 | RESTful + JSON |
| 认证 | JWT Bearer Token |

### 1.2 Git工作流

```
main branch
    │
    ├── hotfix/xxx      # 紧急修复
    ├── feature/xxx     # 新功能开发
    └── bugfix/xxx     # Bug修复
```

### 1.3 提交规范

```
<type>(<scope>): <subject>

Types:
  - feat: 新功能
  - fix: Bug修复
  - refactor: 重构
  - docs: 文档
  - style: 格式
  - test: 测试
  - chore: 构建/辅助工具

Examples:
  feat(monitor): 添加内存趋势图
  fix(gpu): 修复NVIDIA GPU监控为null
  docs(readme): 更新README文档
```

---

## 二、功能开发任务

### Task 1: GPU监控修复

**状态**: ✅ 已完成

**问题**: NVIDIA GPU 利用率、显存、温度返回 null

**解决方案**: 添加 nvidia-smi 作为备选方案

**修改文件**:
- `agent/nodejs/hardware_info/hardware_info.js` - 添加 nvidia-smi 调用逻辑
- `agent/nodejs_hardware.py` - 修复内存 percent 计算

**验证方法**:
```bash
node agent/nodejs/hardware_info/hardware_info.js metrics
# 确认 gpu.percent 不再为 null
```

---

### Task 2: 内存/磁盘IO趋势图

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **后端 - 添加API端点**
   
   文件: `backend/app/api/performance.py`
   
   ```python
   @router.get("/metrics/trend/{device_id}")
   def get_metrics_trend(
       device_id: str,
       metrics: str = Query("cpu,gpu,memory,disk"),  # cpu,gpu,memory,disk
       time_range: str = Query("5m"),  # 1m/5m/15m/1h
       db: Session = Depends(get_db_sync)
   ):
       """获取指标趋势数据"""
       # 计算时间范围
       seconds = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}[time_range]
       since = datetime.utcnow() - timedelta(seconds=seconds)
       
       # 查询数据
       query = select(PerformanceMetric).where(
           PerformanceMetric.device_id == device_id,
           PerformanceMetric.timestamp >= since
       ).order_by(PerformanceMetric.timestamp.asc())
       
       metrics_list = db.execute(query).scalars().all()
       
       # 格式化返回
       return {
           "device_id": device_id,
           "time_range": time_range,
           "metrics": {
               "cpu": [{"timestamp": m.timestamp, "value": m.cpu_percent} for m in metrics_list],
               "gpu": [{"timestamp": m.timestamp, "value": m.gpu_percent} for m in metrics_list],
               "memory": [{"timestamp": m.timestamp, "value": m.memory_percent} for m in metrics_list],
               "disk_read": [{"timestamp": m.timestamp, "value": m.disk_read_mbps} for m in metrics_list],
               "disk_write": [{"timestamp": m.timestamp, "value": m.disk_write_mbps} for m in metrics_list]
           }
       }
   ```

2. **前端 - 添加趋势图组件**
   
   文件: `frontend/src/components/widgets/MemoryTrendChart.vue`
   
   ```vue
   <template>
     <div ref="chartRef" style="height: 250px;"></div>
   </template>
   
   <script setup lang="ts">
   import { ref, onMounted, watch } from 'vue'
   import * as echarts from 'echarts'
   
   const props = defineProps<{
     deviceId: string
     timeRange: string
   }>()
   
   const chartRef = ref<HTMLElement>()
   let chart: echarts.ECharts | null = null
   
   const loadData = async () => {
     const res = await fetch(
       `/api/performance/metrics/trend/${props.deviceId}?time_range=${props.timeRange}`
     )
     const data = await res.json()
     
     const memoryData = data.metrics.memory.map((m: any) => ({
       time: new Date(m.timestamp).toLocaleTimeString(),
       value: m.value
     }))
     
     chart.setOption({
       xAxis: { data: memoryData.map(d => d.time) },
       series: [{ data: memoryData.map(d => d.value) }]
     })
   }
   
   onMounted(() => {
     chart = echarts.init(chartRef.value)
     chart.setOption({ /* 初始化配置 */ })
     loadData()
   })
   </script>
   ```

3. **前端 - 集成到页面**
   
   文件: `frontend/src/views/Performance/Performance.vue`
   
   添加内存和磁盘IO的趋势图卡片

**预计工时**: 2天

**验证方法**:
- 打开性能监控页面
- 确认显示内存趋势图和磁盘IO趋势图

---

### Task 3: 进程监控看板

**状态**: 🔄 待开发

**前置条件**: Agent支持进程采集

**开发步骤**:

1. **Agent - 添加进程采集**
   
   文件: `agent/nodejs/hardware_info/hardware_info.js`
   
   ```javascript
   // 在 getRealtimeMetrics 中添加
   const processes = await si.processes()
   const topProcesses = processes.list
     .sort((a, b) => b.cpu - a.cpu)
     .slice(0, 10)
     .map(p => ({
       name: p.name,
       cpu: Math.round(p.cpu * 100) / 100,
       memory: Math.round(p.mem * 100) / 100,
       pid: p.pid,
       path: p.path
     }))
   
   result.top_processes = JSON.stringify(topProcesses)
   ```

2. **后端 - 进程API**
   
   文件: `backend/app/api/performance.py`
   
   ```python
   @router.get("/processes/{device_id}")
   def get_top_processes(device_id: str, limit: int = 10, db: Session = Depends(get_db_sync)):
       """获取设备Top进程"""
       result = db.execute(
           select(PerformanceMetric)
           .where(PerformanceMetric.device_id == device_id)
           .order_by(PerformanceMetric.timestamp.desc())
           .limit(1)
       ).scalar_one_or_none()
       
       if not result or not result.top_processes:
           return {"processes": []}
       
       import json
       processes = json.loads(result.top_processes)
       return {"processes": processes[:limit]}
   ```

3. **前端 - 进程看板组件**
   
   文件: `frontend/src/components/widgets/ProcessWidget.vue`
   
   表格展示：进程名、CPU%、内存%、PID

**预计工时**: 3天

---

### Task 4: 数据保留策略

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **添加系统配置表**
   
   文件: `backend/app/models/sqlite.py`
   
   ```python
   class SystemConfig(Base):
       __tablename__ = "system_configs"
       
       id = Column(String(36), primary_key=True)
       key = Column(String(100), unique=True, nullable=False)
       value = Column(Text)
       description = Column(String(500))
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   ```

2. **添加配置API**
   
   文件: `backend/app/api/config.py`
   
   ```python
   @router.get("/system-configs")
   def get_configs(db: Session = Depends(get_db_sync)):
       configs = db.execute(select(SystemConfig)).scalars().all()
       return {"items": [{"key": c.key, "value": c.value} for c in configs]}
   
   @router.put("/system-configs/{key}")
   def update_config(key: str, value: str, db: Session = Depends(get_db_sync)):
       config = db.execute(select(SystemConfig).where(SystemConfig.key == key)).scalar_one_or_none()
       if config:
           config.value = value
       else:
           config = SystemConfig(key=key, value=value)
           db.add(config)
       db.commit()
       return {"status": "updated"}
   ```

3. **添加定时清理任务**
   
   文件: `backend/app/core/scheduler.py`
   
   ```python
   @scheduler.scheduled_job("cron", hour=3, minute=0)
   def cleanup_old_metrics():
       """清理过期性能数据"""
       config = get_config("metrics_retention_days", "7")
       cutoff = datetime.utcnow() - timedelta(days=int(config))
       
       db.query(PerformanceMetric).filter(
           PerformanceMetric.timestamp < cutoff
       ).delete()
       db.commit()
   ```

**预计工时**: 2天

---

### Task 5: 新页面布局

**状态**: 🔄 待开发

**前置条件**: 完成设备搜索API

**开发步骤**:

1. **重构性能监控页面**
   
   - 添加搜索框组件
   - 左侧添加设备信息栏
   - 右侧添加监控卡片网格

2. **实现搜索功能**
   
   文件: `backend/app/api/devices.py`
   
   ```python
   @router.get("/devices/search")
   def search_devices(
       q: str = Query(..., description="搜索关键词"),
       department: str = Query(None),
       status: str = Query(None),
       limit: int = Query(10),
       offset: int = Query(0),
       db: Session = Depends(get_db_sync)
   ):
       query = select(Device)
       
       if q:
           query = query.where(
               or_(
                   Device.device_name.ilike(f"%{q}%"),
                   Device.ip_address.ilike(f"%{q}%"),
                   Device.mac_address.ilike(f"%{q}%")
               )
           )
       if department:
           query = query.where(Device.department == department)
       if status:
           query = query.where(Device.status == status)
       
       total = db.execute(select(func.count()).select_from(query.subquery())).scalar()
       items = db.execute(query.offset(offset).limit(limit)).scalars().all()
       
       return {"total": total, "items": items}
   ```

**预计工时**: 5天

---

### Task 6: 远程控制功能

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **添加远程控制命令表**
   
   ```python
   class RemoteCommand(Base):
       __tablename__ = "remote_commands"
       
       id = Column(String(36), primary_key=True)
       device_id = Column(String(36), ForeignKey("devices.id"))
       command_type = Column(String(50))  # shutdown/restart/lock/wol/exec
       params = Column(Text)  # JSON参数
       status = Column(String(20), default="pending")  # pending/executing/completed/failed
       result = Column(Text)
       created_at = Column(DateTime, default=datetime.utcnow)
       executed_at = Column(DateTime)
   ```

2. **添加控制API**
   
   ```python
   @router.post("/devices/{device_id}/control")
   def send_control_command(
       device_id: str,
       command: str,
       params: dict = None,
       db: Session = Depends(get_db_sync)
   ):
       cmd = RemoteCommand(
           device_id=device_id,
           command_type=command,
           params=json.dumps(params or {})
       )
       db.add(cmd)
       db.commit()
       return {"command_id": cmd.id, "status": "pending"}
   ```

3. **Agent添加命令拉取**
   
   ```python
   def poll_commands(device_id):
       while True:
           commands = requests.get(f"{SERVER}/api/devices/{device_id}/commands/pending")
           for cmd in commands.json()["items"]:
               execute_command(cmd)
               report_result(cmd["id"], result)
           time.sleep(5)
   ```

**预计工时**: 5天

---

### Task 7: 增强告警功能

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **添加告警规则表**
   
   ```python
   class AlertRule(Base):
       __tablename__ = "alert_rules"
       
       id = Column(String(36), primary_key=True)
       name = Column(String(100))
       metric_type = Column(String(50))  # cpu/gpu/memory/disk/health
       condition = Column(String(20))  # gt/lt/eq
       threshold = Column(Float)
       duration = Column(Integer)  # 持续多少秒触发
       severity = Column(String(20))  # critical/warning/info
       enabled = Column(Boolean, default=True)
   ```

2. **添加告警服务**
   
   ```python
   def check_alerts(metrics: dict, device_id: str):
       rules = db.query(AlertRule).where(AlertRule.enabled == True).all()
       
       for rule in rules:
           value = get_metric_value(metrics, rule.metric_type)
           if evaluate_condition(value, rule.condition, rule.threshold):
               if check_duration(device_id, rule.metric_type, rule.duration):
                   create_alert(device_id, rule)
   ```

**预计工时**: 3天

---

### Task 8: 审计日志

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **添加审计日志中间件/装饰器**
   
   ```python
   def audit_log(action: str, resource_type: str):
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               result = func(*args, **kwargs)
               
               log = AuditLog(
                   user_id=get_current_user_id(),
                   action=action,
                   resource_type=resource_type,
                   new_value=json.dumps(kwargs),
                   ip_address=get_client_ip()
               )
               db.add(log)
               db.commit()
               
               return result
           return wrapper
       return decorator
   ```

2. **添加日志查询API**
   
   ```python
   @router.get("/audit-logs")
   def get_audit_logs(
       user_id: str = None,
       action: str = None,
       start_time: datetime = None,
       end_time: datetime = None,
       limit: int = 50,
       offset: int = 0
   ):
       # 查询逻辑
       pass
   ```

**预计工时**: 3天

---

### Task 9: RBAC权限管理

**状态**: 🔄 待开发

**前置条件**: 无

**开发步骤**:

1. **扩展用户模型**
   
   ```python
   class User(Base):
       # 现有字段...
       role_id = Column(String(36), ForeignKey("roles.id"))
       department_id = Column(String(36))
   ```

2. **创建角色和权限表**
   
   ```python
   class Role(Base):
       __tablename__ = "roles"
       
       id = Column(String(36), primary_key=True)
       name = Column(String(50), unique=True)
       permissions = Column(JSON)  # ["device:view", "device:manage"]
       is_system = Column(Boolean, default=False)
   ```

3. **添加权限检查装饰器**
   
   ```python
   def require_permission(permission: str):
       def decorator(func):
           @wraps(func)
           def wrapper(*args, **kwargs):
               user = get_current_user()
               if permission not in user.role.permissions:
                   raise HTTPException(403, "权限不足")
               return func(*args, **kwargs)
           return wrapper
       return decorator
   ```

4. **前端权限控制**
   
   ```vue
   <template>
     <button v-if="hasPermission('device:manage')">添加设备</button>
   </template>
   
   <script setup>
   const hasPermission = (perm) => userStore.permissions.includes(perm)
   </script>
   ```

**预计工时**: 5天

---

### Task 10: 设备画像

**状态**: 🔄 待开发

**前置条件**: RBAC完成

**开发步骤**:

1. **扩展设备表**
   
   ```python
   # 添加字段
   ALTER TABLE devices ADD COLUMN department_id VARCHAR(36);
   ALTER TABLE devices ADD COLUMN cost_center VARCHAR(50);
   ALTER TABLE devices ADD COLUMN assigned_user VARCHAR(100);
   ALTER TABLE devices ADD COLUMN position VARCHAR(50);
   ALTER TABLE devices ADD COLUMN location VARCHAR(200);
   ALTER TABLE devices ADD COLUMN purchase_date DATE;
   ALTER TABLE devices ADD COLUMN warranty_expiry DATE;
   ALTER TABLE devices ADD COLUMN supplier VARCHAR(200);
   ALTER TABLE devices ADD COLUMN serial_number VARCHAR(100);
   ALTER TABLE devices ADD COLUMN asset_tag VARCHAR(50);
   ```

2. **创建设备画像API**
   
   ```python
   @router.get("/devices/{device_id}/profile")
   def get_device_profile(device_id: str, db: Session = Depends(get_db_sync)):
       device = db.execute(select(Device).where(Device.id == device_id)).scalar_one_or_none()
       
       # 获取统计数据
       avg_cpu = get_average_usage(device_id, days=30)
       peak_cpu = get_peak_usage(device_id, days=30)
       
       return {
           "basic": {...device.__dict__},
           "usage": {
               "avg_cpu": avg_cpu,
               "peak_cpu": peak_cpu
           }
       }
   ```

**预计工时**: 5天

---

### Task 11: 第三方API集成

**状态**: 🔄 待开发

**前置条件**: RBAC完成

**开发步骤**:

1. **添加API配置表**
   
   ```python
   class ThirdPartyAPI(Base):
       __tablename__ = "third_party_apis"
       
       id = Column(String(36), primary_key=True)
       name = Column(String(100))
       api_type = Column(String(50))  # asset_management/im/notification
       api_url = Column(String(500))
       auth_type = Column(String(50))  # api_key/bearer/oauth/basic
       api_key = Column(String(500))  # 加密存储
       extra_params = Column(JSON)
       enabled = Column(Boolean, default=True)
       last_test = Column(DateTime)
       test_status = Column(String(20))
   ```

2. **添加配置页面API**
   
   ```python
   @router.get("/third-party-apis")
   @router.post("/third-party-apis")
   @router.put("/third-party-apis/{id}")
   @router.delete("/third_party_apis/{id}")
   ```

3. **创建API调用服务**
   
   ```python
   class ThirdPartyService:
       def call_api(self, api_config: ThirdPartyAPI, endpoint: str, params: dict):
           headers = self.build_headers(api_config)
           response = requests.get(f"{api_config.api_url}/{endpoint}", 
                                  headers=headers, params=params)
           return response.json()
   ```

**预计工时**: 3天

---

## 三、开发清单

| Task | 功能 | 预计工时 | 状态 |
|------|------|----------|------|
| 1 | GPU监控修复 | 1天 | ✅ |
| 2 | 内存/磁盘IO趋势图 | 2天 | 🔄 |
| 3 | 进程监控看板 | 3天 | 🔄 |
| 4 | 数据保留策略 | 2天 | 🔄 |
| 5 | 新页面布局 | 5天 | 🔄 |
| 6 | 远程控制 | 5天 | 🔄 |
| 7 | 增强告警 | 3天 | 🔄 |
| 8 | 审计日志 | 3天 | 🔄 |
| 9 | RBAC权限管理 | 5天 | 🔄 |
| 10 | 设备画像 | 5天 | 🔄 |
| 11 | 第三方API集成 | 3天 | 🔄 |

**总计**: 37天

---

## 四、代码审查清单

每次功能开发完成后，需要进行以下审查：

### 4.1 功能性
- [ ] 功能是否按需求实现？
- [ ] API返回值格式是否正确？
- [ ] 前端数据展示是否正确？
- [ ] 错误处理是否完善？

### 4.2 安全性
- [ ] 是否有SQL注入风险？
- [ ] 敏感数据是否加密存储？
- [ ] 权限检查是否到位？
- [ ] 输入验证是否完善？

### 4.3 性能
- [ ] 数据库查询是否有索引？
- [ ] 是否有N+1查询问题？
- [ ] 大数据量是否有分页？
- [ ] 缓存策略是否合理？

### 4.4 代码质量
- [ ] 命名是否规范？
- [ ] 注释是否完整？
- [ ] 是否有重复代码？
- [ ] 异常处理是否合理？

---

**文档版本历史**

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| 1.0 | 2026-03-08 | 初始版本 |

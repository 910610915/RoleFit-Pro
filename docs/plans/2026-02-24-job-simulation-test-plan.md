# 岗位模拟测试系统 - 开发计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有硬件基准测试系统上新增岗位模拟测试功能，支持自动化脚本模拟员工真实工作场景

**Architecture:** 采用模块化设计，新增岗位/软件/脚本/执行记录四大模块，与现有任务系统解耦，通过task_category区分基准测试和岗位模拟测试

**Tech Stack:** FastAPI + SQLAlchemy + Vue3 + Python自动化(pywinauto/psutil)

---

## Phase 1: 数据模型 (数据库层)

### Task 1: 创建岗位模型

**Files:**
- Modify: `backend/app/models/sqlite.py` (追加Position模型)
- Test: `backend/app/models/test_position.py`

**Step 1: 添加Position模型到sqlite.py**

在文件末尾添加:

```python
class Position(Base):
    """岗位配置模型"""
    __tablename__ = "positions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    position_name = Column(String(100), nullable=False)
    position_code = Column(String(50), unique=True, nullable=False)
    department = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 2: 添加到Base.metadata**

确保所有模型都在 `Base.metadata` 中

**Step 3: 运行数据库迁移**

```bash
cd backend
python init_sqlite.py
```

**Step 4: 验证表创建**

```bash
sqlite3 hardware_benchmark.db ".tables"
# 应包含 positions
```

---

### Task 2: 创建测试软件模型

**Files:**
- Modify: `backend/app/models/sqlite.py`

**Step 1: 添加TestSoftware模型**

```python
class TestSoftware(Base):
    """测试软件模型"""
    __tablename__ = "test_software"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    software_name = Column(String(200), nullable=False)
    software_code = Column(String(50), unique=True, nullable=False)
    vendor = Column(String(100), nullable=True)
    category = Column(String(20), nullable=True)  # DEV/ART/ANIM/VFX/TOOL/OFFICE
    install_path = Column(String(500), nullable=True)
    launch_params = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

---

### Task 3: 创建测试脚本模型

**Files:**
- Modify: `backend/app/models/sqlite.py`

**Step 1: 添加JobScript模型**

```python
class JobScript(Base):
    """岗位测试脚本模型"""
    __tablename__ = "job_scripts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_name = Column(String(200), nullable=False)
    script_code = Column(String(50), unique=True, nullable=False)
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=True)
    software_id = Column(String(36), ForeignKey("test_software.id"), nullable=True)
    script_type = Column(String(20), nullable=True)  # START/OPERATION/RENDER/STRESS
    script_content = Column(Text, nullable=False)  # JSON字符串
    expected_duration = Column(Integer, default=300)  # 秒
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

---

### Task 4: 创建执行记录和指标模型

**Files:**
- Modify: `backend/app/models/sqlite.py`

**Step 1: 添加ScriptExecution模型**

```python
class ScriptExecution(Base):
    """脚本执行记录"""
    __tablename__ = "script_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("test_tasks.id"), nullable=True)
    script_id = Column(String(36), ForeignKey("job_scripts.id"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    exit_code = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

**Step 2: 添加SoftwareMetrics模型**

```python
class SoftwareMetrics(Base):
    """软件运行指标"""
    __tablename__ = "software_metrics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    execution_id = Column(String(36), ForeignKey("script_executions.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    software_name = Column(String(200), nullable=True)
    process_id = Column(Integer, nullable=True)
    cpu_percent = Column(Float, nullable=True)
    memory_mb = Column(Float, nullable=True)
    gpu_percent = Column(Float, nullable=True)
    gpu_memory_mb = Column(Float, nullable=True)
    disk_read_mbps = Column(Float, nullable=True)
    disk_write_mbps = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)  # RUNNING/IDLE/CRASHED
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

---

## Phase 2: API层

### Task 5: 创建岗位API

**Files:**
- Create: `backend/app/api/positions.py`
- Modify: `backend/app/main.py` (注册路由)
- Test: 使用curl测试

**Step 1: 创建positions.py**

```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.core.database import get_db
from app.models.sqlite import Position
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse, PositionListResponse

router = APIRouter(prefix="/positions", tags=["Positions"])

@router.get("", response_model=PositionListResponse)
async def list_positions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Position).where(Position.is_active == True)
    if department:
        query = query.where(Position.department == department)
    
    # Count
    from sqlalchemy import func
    count_result = await db.execute(select(func.count(Position.id)))
    total = count_result.scalar() or 0
    
    # Paginate
    query = query.order_by(Position.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PositionListResponse(total=total, page=page, page_size=page_size, items=items)

@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db)):
    position = Position(**data.model_dump())
    db.add(position)
    await db.commit()
    await db.refresh(position)
    return position

@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position

@router.put("/{position_id}", response_model=PositionResponse)
async def update_position(position_id: str, data: PositionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(position, key, value)
    
    await db.commit()
    await db.refresh(position)
    return position

@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(position_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Position).where(Position.id == position_id))
    position = result.scalar_one_or_none()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    position.is_active = False
    await db.commit()
    return None
```

**Step 2: 注册路由到main.py**

```python
from app.api import positions
# 在app.include_router后添加
app.include_router(positions.router, prefix="/api", tags=["Positions"])
```

**Step 3: 创建schemas**

Create: `backend/app/schemas/position.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PositionBase(BaseModel):
    position_name: str
    position_code: str
    department: Optional[str] = None
    description: Optional[str] = None

class PositionCreate(PositionBase):
    pass

class PositionUpdate(BaseModel):
    position_name: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class PositionResponse(PositionBase):
    id: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class PositionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[PositionResponse]
```

**Step 4: 测试API**

```bash
curl http://localhost:8000/api/positions
# 预期: {"total":0,"page":1,"page_size":20,"items":[]}
```

---

### Task 6: 创建软件管理API

**Files:**
- Create: `backend/app/api/software.py`
- Create: `backend/app/schemas/software.py`
- Modify: `backend/app/main.py`

按照Task 5的结构创建，参考以下字段:
- software_name, software_code, vendor, category, install_path, launch_params

---

### Task 7: 创建脚本管理API

**Files:**
- Create: `backend/app/api/scripts.py`
- Create: `backend/app/schemas/script.py`
- Modify: `backend/app/main.py`

按照Task 5的结构创建

---

### Task 8: 创建执行记录API

**Files:**
- Create: `backend/app/api/executions.py`
- Create: `backend/app/schemas/execution.py`

---

## Phase 3: 前端页面

### Task 9: 创建岗位管理页面

**Files:**
- Create: `frontend/src/views/Positions/PositionList.vue`
- Create: `frontend/src/views/Positions/PositionEdit.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/App.vue` (菜单)

**Step 1: 创建PositionList.vue**

```vue
<template>
  <div class="position-list">
    <div class="header">
      <n-h1>岗位管理</n-h1>
      <n-button type="primary" @click="router.push('/positions/create')">
        新增岗位
      </n-button>
    </div>
    
    <n-card>
      <n-space>
        <n-select v-model="filters.department" placeholder="部门" :options="deptOptions" clearable style="width: 150px" />
        <n-button @click="loadPositions">搜索</n-button>
      </n-space>
    </n-card>
    
    <n-card style="margin-top: 16px">
      <n-data-table :columns="columns" :data="positions" :loading="loading" :pagination="pagination" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NH1, NButton, NCard, NSpace, NSelect, NDataTable, NTag, NIcon } from 'naive-ui'
import { Create, Trash, Edit } from '@vicons/ionicons5'

const router = useRouter()
const positions = ref([])
const loading = ref(false)
const filters = reactive({ department: null })

const deptOptions = [
  { label: '技术部', value: '技术部' },
  { label: '美术部', value: '美术部' },
  { label: '策划部', value: '策划部' },
  { label: '运营部', value: '运营部' }
]

const columns = [
  { title: '岗位名称', key: 'position_name' },
  { title: '岗位代码', key: 'position_code' },
  { title: '部门', key: 'department' },
  { title: '描述', key: 'description' },
  { 
    title: '操作', 
    key: 'actions',
    width: 120,
    render: (row: any) => h(NSpace, { size: 'small' }, () => [
      h(NButton, { size: 'small', onClick: () => router.push(`/positions/${row.id}`) }, () => h(NIcon, null, () => h(Edit))),
      h(NButton, { size: 'small', onClick: () => handleDelete(row.id) }, () => h(NIcon, null, () => h(Trash)))
    ])
  }
]

const loadPositions = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/positions')
    positions.value = await res.json()
  } finally {
    loading.value = false
  }
}

onMounted(loadPositions)
</script>
```

**Step 2: 添加路由**

```typescript
{
  path: '/positions',
  name: 'PositionList',
  component: () => import('@/views/Positions/PositionList.vue'),
  meta: { requiresAuth: true }
}
```

**Step 3: 添加菜单项**

在App.vue的menuOptions中添加

---

### Task 10: 创建软件管理页面

**Files:**
- Create: `frontend/src/views/Software/SoftwareList.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/App.vue`

---

### Task 11: 创建脚本管理页面

**Files:**
- Create: `frontend/src/views/Scripts/ScriptList.vue`
- Modify: `frontend/src/router/index.ts`

---

## Phase 4: 预置数据

### Task 12: 初始化预设岗位和软件

**Files:**
- Create: `backend/init_positions.py`

**Step 1: 创建预设数据脚本**

```python
"""初始化预设岗位和软件数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.sqlite import Position, TestSoftware, JobScript, Base
import uuid

def init_preset_data():
    db_path = os.path.join(os.path.dirname(__file__), "hardware_benchmark.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 创建岗位
    positions_data = [
        {"name": "UE开发", "code": "UE_DEV", "dept": "技术部"},
        {"name": "Unity开发", "code": "UNITY_DEV", "dept": "技术部"},
        {"name": "C++开发", "code": "CPP_DEV", "dept": "技术部"},
        {"name": "3D美术", "code": "3D_ART", "dept": "美术部"},
        {"name": "原画", "code": "CONCEPT_ART", "dept": "美术部"},
        {"name": "特效", "code": "VFX", "dept": "美术部"},
        {"name": "动画", "code": "ANIM", "dept": "美术部"},
        {"name": "UI设计", "code": "UI_DESIGN", "dept": "设计部"},
        {"name": "产品经理", "code": "PM", "dept": "策划部"},
        {"name": "行政", "code": "ADMIN", "dept": "行政部"},
    ]
    
    # 创建软件
    software_data = [
        {"name": "Unreal Engine 5", "code": "UE5", "vendor": "Epic Games", "category": "DEV"},
        {"name": "Unity 2023", "code": "UNITY", "vendor": "Unity Technologies", "category": "DEV"},
        {"name": "Visual Studio 2022", "code": "VS2022", "vendor": "Microsoft", "category": "DEV"},
        {"name": "Photoshop 2024", "code": "PS2024", "vendor": "Adobe", "category": "ART"},
        {"name": "Maya 2024", "code": "MAYA", "vendor": "Autodesk", "category": "ART"},
        {"name": "3ds Max 2024", "code": "MAX2024", "vendor": "Autodesk", "category": "ART"},
        {"name": "After Effects", "code": "AE", "vendor": "Adobe", "category": "VFX"},
        {"name": "Figma", "code": "FIGMA", "vendor": "Figma", "category": "TOOL"},
        {"name": "Excel 365", "code": "EXCEL", "vendor": "Microsoft", "category": "OFFICE"},
    ]
    
    # ... 添加到数据库
    
    print("预设数据初始化完成")
    session.close()

if __name__ == "__main__":
    init_preset_data()
```

**Step 2: 运行脚本**

```bash
cd backend
python init_positions.py
```

---

## Phase 5: 测试与验证

### Task 13: 端到端测试

**Step 1: 测试岗位CRUD**

```bash
# 创建岗位
curl -X POST http://localhost:8000/api/positions \
  -H "Content-Type: application/json" \
  -d '{"position_name":"测试岗位","position_code":"TEST","department":"技术部"}'

# 获取列表
curl http://localhost:8000/api/positions

# 更新
curl -X PUT http://localhost:8000/api/positions/{id} \
  -H "Content-Type: application/json" \
  -d '{"department":"测试部"}'

# 删除
curl -X DELETE http://localhost:8000/api/positions/{id}
```

**Step 2: 测试前端页面**

1. 访问 http://localhost:5173
2. 登录账号
3. 检查侧边栏是否有"岗位管理"菜单
4. 点击进入岗位管理页面
5. 测试新增/编辑/删除功能

---

## 执行方式

**Plan complete and saved to `docs/plans/2026-02-24-job-simulation-test-plan.md`**

**Two execution options:**

1. **Subagent-Driven (当前会话)** - 我为每个任务派遣子代理,任务间进行代码审查,快速迭代

2. **Parallel Session (新会话)** - 在新会话中使用executing-plans,批量执行带检查点

**你选择哪种方式?**

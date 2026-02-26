# RoleFit Pro 功能增强设计文档

**日期**: 2026-02-26  
**版本**: v1.0

---

## 1. 概述

对RoleFit Pro进行以下功能增强：
1. 主页UI改版 - 与宣传首页风格统一
2. 开放注册功能
3. 用户信息展示和退出登录
4. 后台管理界面（功能卡片配置）
5. 数据库迁移功能（支持多数据库格式）

---

## 2. UI/UX设计

### 2.1 主页改版

**设计目标**：专业管理后台风格，与宣传首页统一

**视觉规范**：
- 背景：白色 + 3D粒子效果（复用ParticleBackgroundWhite组件）
- 字体：黑色文字（#1a1a1a）
- 卡片：白色背景、圆角阴影、专业图标

**布局结构**：
```
┌─────────────────────────────────────────┐
│  顶部导航栏 (Logo + 导航 + 用户信息)      │
├─────────────────────────────────────────┤
│  3D粒子背景                              │
├─────────────────────────────────────────┤
│  统计卡片区域 (可配置显示哪些)            │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐          │
│  │设备│ │任务│ │测试│ │分数│          │
│  └────┘ └────┘ └────┘ └────┘          │
├─────────────────────────────────────────┤
│  功能卡片区域 (可配置、可拖拽排序)        │
│  ┌────────┐ ┌────────┐ ┌────────┐     │
│  │设备管理│ │岗位管理│ │软件管理│     │
│  └────────┘ └────────┘ └────────┘     │
│  ┌────────┐ ┌────────┐ ┌────────┐     │
│  │脚本管理│ │任务管理│ │执行记录│     │
│  └────────┘ └────────┘ └────────┘     │
│  ┌────────┐ ┌────────┐                │
│  │设备对比│ │ 数据分析│                │
│  └────────┘ └────────┘                │
└─────────────────────────────────────────┘
```

**卡片样式**：
- 尺寸：响应式网格（2-4列）
- 圆角：16px
- 阴影：0 4px 20px rgba(0,0,0,0.08)
- 图标：64px专业图标
- 悬停效果：上浮 + 阴影加深

### 2.2 登录/注册

**登录弹窗**：
- 标题：RoleFit Pro
- 表单：用户名、密码
- 按钮：登录（渐变色）、注册入口
- 记住我选项

**注册弹窗**：
- 表单：用户名、密码、确认密码、邮箱（可选）、部门（可选）
- 按钮：注册、返回登录

### 2.3 用户信息区（左下角）

**布局**：
```
┌────────────────────────┐
│ [图标] 用户名         │
│        [退出登录]    │
└────────────────────────┘
```
- 位置：页面左下角固定
- 样式：半透明背景、圆角

### 2.4 后台管理界面

**入口**：设置页面 或 专门的系统管理入口

**功能**：
1. **功能卡片管理**
   - 显示/隐藏开关
   - 修改标题、描述
   - 选择图标（图标选择器）
   - 拖拽排序
   - 新增自定义卡片
   - 删除自定义卡片

2. **数据库管理**
   - 导出为SQLite文件
   - 导出为MySQL兼容SQL
   - 导出为PostgreSQL兼容SQL
   - 导入数据库

---

## 3. 技术设计

### 3.1 数据模型

**用户表扩展**：
```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    department TEXT,
    role TEXT DEFAULT 'user',  -- admin, user
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**功能卡片配置表**：
```sql
-- 功能卡片配置
CREATE TABLE feature_cards (
    id TEXT PRIMARY KEY,
    card_key TEXT UNIQUE NOT NULL,  -- device, position, software, etc.
    title TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    is_visible BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    is_custom BOOLEAN DEFAULT FALSE,  -- 是否自定义卡片
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 API设计

**用户相关**：
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息

**功能卡片配置**：
- `GET /api/feature-cards` - 获取所有卡片配置
- `PUT /api/feature-cards/{id}` - 更新卡片配置
- `POST /api/feature-cards` - 新增自定义卡片
- `DELETE /api/feature-cards/{id}` - 删除自定义卡片

**数据库导出/导入**：
- `GET /api/db/export/sqlite` - 导出SQLite文件
- `GET /api/db/export/mysql` - 导出MySQL格式SQL
- `GET /api/db/export/postgresql` - 导出PostgreSQL格式SQL
- `POST /api/db/import` - 导入数据库

### 3.3 前端路由

```
/login          - 登录页（宣传首页）
/dashboard      - 主页（改版后）
/settings       - 设置/后台管理
```

---

## 4. 数据库迁移格式说明

### 4.1 MySQL兼容导出

| SQLite类型 | MySQL类型 |
|-----------|----------|
| INTEGER | INT |
| TEXT | TEXT / VARCHAR(255) |
| REAL | DOUBLE |
| BLOB | BLOB |
| BOOLEAN | TINYINT(1) |
| DATETIME | DATETIME |

### 4.2 PostgreSQL兼容导出

| SQLite类型 | PostgreSQL类型 |
|-----------|---------------|
| INTEGER | INTEGER / BIGINT |
| TEXT | TEXT |
| REAL | DOUBLE PRECISION |
| BLOB | BYTEA |
| BOOLEAN | BOOLEAN |
| DATETIME | TIMESTAMP |

---

## 5. 实现优先级

1. **注册功能** - 后端API + 前端注册弹窗
2. **用户信息区** - 左下角用户信息 + 退出登录
3. **主页改版** - UI样式统一
4. **后台管理** - 功能卡片配置
5. **数据库迁移** - 导出/导入功能

---

## 6. 验收标准

- [ ] 用户可以成功注册账号
- [ ] 登录后左下角显示用户名和退出按钮
- [ ] 主页UI风格与宣传首页统一（白色背景、粒子效果、专业卡片）
- [ ] 可以在后台管理系统中配置功能卡片的显示/隐藏
- [ ] 可以修改功能卡片的标题和描述
- [ ] 可以导出SQLite文件
- [ ] 可以导出MySQL兼容SQL
- [ ] 可以导出PostgreSQL兼容SQL
- [ ] 可以导入数据库

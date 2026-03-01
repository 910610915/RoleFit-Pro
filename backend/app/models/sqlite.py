"""
SQLite兼容的数据库模型
用于无需安装PostgreSQL的轻量部署
"""

import uuid
import json
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base

# 创建独立的Base
Base = declarative_base()


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    devices = relationship("Device", back_populates="owner")
    test_tasks = relationship("TestTask", back_populates="creator")
    test_scripts = relationship("TestScript", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Device(Base):
    """设备模型"""

    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_name = Column(String(100), nullable=False)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String(15), nullable=True)
    hostname = Column(String(100), nullable=True)

    # 硬件信息
    cpu_model = Column(String(200), nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    cpu_threads = Column(Integer, nullable=True)
    cpu_base_clock = Column(Float, nullable=True)

    gpu_model = Column(String(200), nullable=True)
    gpu_vram_mb = Column(Integer, nullable=True)
    gpu_driver_version = Column(String(50), nullable=True)
    all_gpus = Column(Text, nullable=True)  # JSON: 所有显卡信息

    ram_total_gb = Column(Float, nullable=True)
    ram_frequency = Column(Integer, nullable=True)
    all_memory = Column(Text, nullable=True)  # JSON: 所有内存条信息

    disk_model = Column(String(200), nullable=True)
    disk_capacity_tb = Column(Float, nullable=True)
    disk_type = Column(String(20), nullable=True)
    all_disks = Column(Text, nullable=True)  # JSON: 所有磁盘信息

    os_name = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    os_build = Column(String(20), nullable=True)

    # 关联
    department = Column(String(100), nullable=True, index=True)
    position = Column(String(100), nullable=True, index=True)
    assigned_to = Column(String(100), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # 状态
    status = Column(String(20), default="offline", index=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    notes = Column(Text, nullable=True)

    owner = relationship("User", back_populates="devices")
    test_results = relationship("TestResult", back_populates="device")


class PositionStandard(Base):
    """岗位配置标准"""

    __tablename__ = "position_standards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    position_name = Column(String(100), unique=True, nullable=False)
    position_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # CPU要求
    cpu_min_cores = Column(Integer, nullable=True)
    cpu_min_threads = Column(Integer, nullable=True)
    cpu_min_score = Column(Integer, nullable=True)
    cpu_max_usage_percent = Column(Float, default=80.0)

    # 内存要求
    ram_min_gb = Column(Float, nullable=True)
    ram_max_usage_percent = Column(Float, default=85.0)

    # GPU要求
    gpu_model_pattern = Column(String(200), nullable=True)
    gpu_min_vram_mb = Column(Integer, nullable=True)
    gpu_min_score = Column(Integer, nullable=True)
    gpu_max_usage_percent = Column(Float, default=90.0)

    # 存储要求
    disk_min_capacity_tb = Column(Float, nullable=True)
    disk_min_read_mbps = Column(Float, nullable=True)
    disk_min_write_mbps = Column(Float, nullable=True)
    disk_min_iops = Column(Integer, nullable=True)

    # 业务场景要求
    compile_time_max_seconds = Column(Integer, nullable=True)
    viewport_fps_min = Column(Integer, nullable=True)
    render_time_max_seconds = Column(Integer, nullable=True)
    app_launch_max_seconds = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    creator = relationship("User")
    test_results = relationship("TestResult", back_populates="standard")


class TestTask(Base):
    """测试任务"""

    __tablename__ = "test_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False)
    task_status = Column(String(20), default="pending", index=True)

    # 目标设备
    target_device_ids = Column(Text, default="[]")  # JSON字符串
    target_departments = Column(Text, default="[]")
    target_positions = Column(Text, default="[]")

    # 测试配置
    test_script_id = Column(String(36), ForeignKey("test_scripts.id"), nullable=True)
    test_duration_seconds = Column(Integer, nullable=True)
    sample_interval_ms = Column(Integer, default=1000)

    # 执行信息
    assigned_agent_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 调度
    schedule_type = Column(String(20), nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    cron_expression = Column(String(100), nullable=True)

    # 创建者
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    creator = relationship("User", back_populates="test_tasks")
    script = relationship("TestScript")
    results = relationship("TestResult", back_populates="task")


class TestScript(Base):
    """测试脚本"""

    __tablename__ = "test_scripts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_name = Column(String(200), nullable=False)
    script_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    target_positions = Column(Text, default="[]")
    script_type = Column(String(20), default="operation")
    script_content = Column(Text, nullable=False)  # JSON字符串

    timeout_seconds = Column(Integer, default=3600)
    retry_count = Column(Integer, default=0)

    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    creator = relationship("User", back_populates="test_scripts")


class TestResult(Base):
    """测试结果"""

    __tablename__ = "test_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("test_tasks.id"), nullable=True, index=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True, index=True)

    test_type = Column(String(50), nullable=True)
    test_status = Column(String(20), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, nullable=False)

    # 分数
    overall_score = Column(Float, nullable=True)
    cpu_score = Column(Float, nullable=True)
    gpu_score = Column(Float, nullable=True)
    memory_score = Column(Float, nullable=True)
    disk_score = Column(Float, nullable=True)

    # 标准检查
    is_standard_met = Column(Boolean, nullable=True)
    standard_id = Column(String(36), ForeignKey("position_standards.id"), nullable=True)
    fail_reasons = Column(Text, nullable=True)  # JSON字符串

    # 性能摘要
    performance_summary = Column(Text, nullable=True)

    # 瓶颈分析
    bottleneck_type = Column(String(50), nullable=True)
    bottleneck_detail = Column(Text, nullable=True)

    # 升级建议
    upgrade_suggestion = Column(Text, nullable=True)

    result_file_path = Column(String(500), nullable=True)
    log_file_path = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    task = relationship("TestTask", back_populates="results")
    device = relationship("Device", back_populates="test_results")
    standard = relationship("PositionStandard", back_populates="test_results")


class AuditLog(Base):
    """审计日志"""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")


class SystemConfig(Base):
    """系统配置"""

    __tablename__ = "system_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), default="string")
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)


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
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class TestSoftware(Base):
    """测试软件模型"""

    __tablename__ = "test_software"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    software_name = Column(String(200), nullable=False)
    software_code = Column(String(50), unique=True, nullable=False)
    vendor = Column(String(100), nullable=True)
    category = Column(String(20), nullable=True)  # DEV/ART/ANIM/VFX/TOOL/OFFICE
    icon = Column(String(500), nullable=True)  # 图标路径

    # ====== 安装配置 ======
    # 软件类型: installer(安装包) / portable(绿色版)
    software_type = Column(String(20), default="portable")
    # 安装包格式: exe / msi / zip / rar / 7z
    package_format = Column(String(20), nullable=True)
    # 服务器存储路径 (相对于软件根目录)
    storage_path = Column(String(500), nullable=True)
    # 目标机器安装目录
    target_install_path = Column(String(500), nullable=True)
    # 安装后子文件夹名称
    subfolder_name = Column(String(100), nullable=True)
    # 静默安装命令
    silent_install_cmd = Column(String(500), nullable=True)
    # 主程序相对路径（用于启动）
    main_exe_relative_path = Column(String(500), nullable=True)

    # ====== 检测配置 ======
    # 检测方式: process / registry / file
    detection_method = Column(String(20), default="file")
    # 检测路径（file方式）
    detection_path = Column(String(500), nullable=True)
    # 检测关键字（process或registry方式）
    detection_keyword = Column(String(200), nullable=True)

    # ====== 其他 ======
    version = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    launch_params = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class JobScript(Base):
    """岗位测试脚本模型"""

    __tablename__ = "job_scripts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    script_name = Column(String(200), nullable=False)
    script_code = Column(String(50), unique=True, nullable=False)
    position_id = Column(
        String(36), ForeignKey("positions.id"), nullable=True
    )  # 兼容旧字段
    position_ids = Column(Text, nullable=True)  # 新字段：多岗位(JSON数组)
    software_id = Column(String(36), ForeignKey("test_software.id"), nullable=True)
    script_type = Column(String(20), nullable=True)  # START/OPERATION/RENDER/STRESS
    script_content = Column(Text, nullable=False)  # JSON字符串
    expected_duration = Column(Integer, default=300)  # 秒
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


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


class AlarmRule(Base):
    """告警规则"""

    __tablename__ = "alarm_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    alarm_type = Column(
        String(50), nullable=False
    )  # device_offline, test_failed, score_low, etc.
    condition = Column(Text, nullable=False)  # JSON condition
    threshold = Column(Float, nullable=True)
    enabled = Column(Boolean, default=True)
    notification_channels = Column(
        Text, nullable=True
    )  # JSON array: email, sms, webhook
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Alarm(Base):
    """告警记录"""

    __tablename__ = "alarms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("alarm_rules.id"), nullable=True)
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=True)
    alarm_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # info, warning, error, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class FeatureCard(Base):
    """功能卡片配置"""

    __tablename__ = "feature_cards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    card_key = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    route = Column(String(100), nullable=True)
    is_visible = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PerformanceMetric(Base):
    """实时性能指标"""

    __tablename__ = "performance_metrics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)

    # 时间戳
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    # CPU 指标
    cpu_percent = Column(Float, nullable=True)
    cpu_temperature = Column(Float, nullable=True)
    cpu_power_watts = Column(Float, nullable=True)
    cpu_frequency_mhz = Column(Float, nullable=True)

    # GPU 指标
    gpu_percent = Column(Float, nullable=True)
    gpu_temperature = Column(Float, nullable=True)
    gpu_power_watts = Column(Float, nullable=True)
    gpu_frequency_mhz = Column(Float, nullable=True)
    gpu_memory_used_mb = Column(Float, nullable=True)
    gpu_memory_total_mb = Column(Float, nullable=True)

    # 内存指标
    memory_percent = Column(Float, nullable=True)
    memory_used_mb = Column(Float, nullable=True)
    memory_available_mb = Column(Float, nullable=True)

    # 磁盘指标
    disk_read_mbps = Column(Float, nullable=True)
    disk_write_mbps = Column(Float, nullable=True)
    disk_io_percent = Column(Float, nullable=True)

    # 网络指标
    network_sent_mbps = Column(Float, nullable=True)
    network_recv_mbps = Column(Float, nullable=True)

    # 进程信息
    process_count = Column(Integer, nullable=True)
    top_processes = Column(
        Text, nullable=True
    )  # JSON: [{"name": "xxx", "cpu": 10, "memory": 500}]

    # 附加数据
    raw_data = Column(Text, nullable=True)  # 原始采集数据 JSON

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SoftwareBenchmark(Base):
    """软件基准测试结果"""

    __tablename__ = "software_benchmarks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)
    software_code = Column(
        String(50), nullable=False, index=True
    )  # blender, maya, unreal, etc.

    # 测试信息
    benchmark_type = Column(
        String(50), nullable=False
    )  # render, compile, launch, viewport
    test_scene = Column(String(200), nullable=True)  # 测试场景/项目名称
    scene_file_path = Column(String(500), nullable=True)

    # 时间
    timestamp = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, nullable=True)

    # 性能结果
    score = Column(Float, nullable=True)  # 综合分数
    score_cpu = Column(Float, nullable=True)
    score_gpu = Column(Float, nullable=True)
    score_memory = Column(Float, nullable=True)
    score_disk = Column(Float, nullable=True)

    # 详细指标
    avg_fps = Column(Float, nullable=True)
    min_fps = Column(Float, nullable=True)
    max_fps = Column(Float, nullable=True)
    frame_count = Column(Integer, nullable=True)
    render_time_seconds = Column(Float, nullable=True)

    # 资源峰值
    peak_cpu_percent = Column(Float, nullable=True)
    peak_gpu_percent = Column(Float, nullable=True)
    peak_memory_mb = Column(Float, nullable=True)
    peak_gpu_memory_mb = Column(Float, nullable=True)

    # 平均资源
    avg_cpu_percent = Column(Float, nullable=True)
    avg_gpu_percent = Column(Float, nullable=True)
    avg_memory_mb = Column(Float, nullable=True)

    # 状态
    status = Column(String(20), nullable=True)  # success, failed, timeout
    error_message = Column(Text, nullable=True)
    log_file_path = Column(String(500), nullable=True)

    # 瓶颈分析
    bottleneck_type = Column(String(50), nullable=True)  # cpu, gpu, memory, disk, io
    bottleneck_detail = Column(Text, nullable=True)

    # 升级建议
    upgrade_suggestion = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ControlCommand(Base):
    """控制命令"""

    __tablename__ = "control_commands"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)

    # 命令信息
    command_type = Column(
        String(50), nullable=False
    )  # start_benchmark, stop_task, restart_agent
    target_software = Column(String(100), nullable=True)  # 目标软件
    command_params = Column(Text, nullable=True)  # JSON 参数

    # 状态
    status = Column(
        String(20), default="pending", index=True
    )  # pending, sent, executing, completed, failed
    priority = Column(Integer, default=5)  # 优先级 1-10

    # 执行信息
    sent_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 结果
    result = Column(Text, nullable=True)  # JSON 结果
    error_message = Column(Text, nullable=True)

    # 来源
    source = Column(String(50), nullable=True)  # manual, scheduler, ai_analysis
    triggered_by = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class PerformanceAlert(Base):
    """性能告警"""

    __tablename__ = "performance_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)

    # 告警信息
    alert_type = Column(
        String(50), nullable=False
    )  # high_cpu, high_gpu, high_memory, disk_slow, etc.
    severity = Column(String(20), nullable=False)  # info, warning, error, critical

    # 阈值
    metric_name = Column(
        String(50), nullable=False
    )  # cpu_percent, gpu_percent, memory_percent
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)

    # 详情
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)  # AI 建议

    # 状态
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)

    # 关联
    benchmark_id = Column(
        String(36), ForeignKey("software_benchmarks.id"), nullable=True
    )

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AIAnalysisReport(Base):
    """AI 分析报告"""

    __tablename__ = "ai_analysis_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = Column(String(36), ForeignKey("devices.id"), nullable=False, index=True)

    # 分析类型
    analysis_type = Column(
        String(50), nullable=False
    )  # performance_trend, bottleneck, upgrade_recommendation
    title = Column(String(200), nullable=False)

    # 摘要
    summary = Column(Text, nullable=True)

    # 详细内容 (JSON)
    details = Column(Text, nullable=True)

    # 结论和建议
    conclusions = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)

    # 状态
    status = Column(String(20), nullable=True)  # pending, completed, failed

    # 关联分析
    related_metrics = Column(Text, nullable=True)  # JSON: 相关的性能指标ID列表
    related_benchmarks = Column(Text, nullable=True)  # JSON: 相关的基准测试ID列表

    # AI 元数据
    model_used = Column(String(100), nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

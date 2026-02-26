import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user")  # admin, operator, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    devices = relationship("Device", back_populates="owner")
    test_tasks = relationship("TestTask", back_populates="creator")
    test_scripts = relationship("TestScript", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class Device(Base):
    """Device model for managed computers"""
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String(100), nullable=False)
    mac_address = Column(String(17), unique=True, nullable=False, index=True)
    ip_address = Column(String(15), nullable=True)
    hostname = Column(String(100), nullable=True)
    
    # Hardware Info
    cpu_model = Column(String(200), nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    cpu_threads = Column(Integer, nullable=True)
    cpu_base_clock = Column(Float, nullable=True)
    
    gpu_model = Column(String(200), nullable=True)
    gpu_vram_mb = Column(Integer, nullable=True)
    gpu_driver_version = Column(String(50), nullable=True)
    
    ram_total_gb = Column(Float, nullable=True)
    ram_frequency = Column(Integer, nullable=True)
    
    disk_model = Column(String(200), nullable=True)
    disk_capacity_tb = Column(Float, nullable=True)
    disk_type = Column(String(20), nullable=True)  # NVMe, SATA, SSD, HDD
    
    os_name = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)
    os_build = Column(String(20), nullable=True)
    
    # Association
    department = Column(String(100), nullable=True, index=True)
    position = Column(String(100), nullable=True, index=True)
    assigned_to = Column(String(100), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Status
    status = Column(String(20), default="offline", index=True)  # online, offline, testing, error
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="devices")
    test_results = relationship("TestResult", back_populates="device")


class PositionStandard(Base):
    """Position configuration standards"""
    __tablename__ = "position_standards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    position_name = Column(String(100), unique=True, nullable=False)
    position_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # CPU Requirements
    cpu_min_cores = Column(Integer, nullable=True)
    cpu_min_threads = Column(Integer, nullable=True)
    cpu_min_score = Column(Integer, nullable=True)
    cpu_max_usage_percent = Column(Float, default=80.0)
    
    # Memory Requirements
    ram_min_gb = Column(Float, nullable=True)
    ram_max_usage_percent = Column(Float, default=85.0)
    
    # GPU Requirements
    gpu_model_pattern = Column(String(200), nullable=True)
    gpu_min_vram_mb = Column(Integer, nullable=True)
    gpu_min_score = Column(Integer, nullable=True)
    gpu_max_usage_percent = Column(Float, default=90.0)
    
    # Storage Requirements
    disk_min_capacity_tb = Column(Float, nullable=True)
    disk_min_read_mbps = Column(Float, nullable=True)
    disk_min_write_mbps = Column(Float, nullable=True)
    disk_min_iops = Column(Integer, nullable=True)
    
    # Business Scenario Requirements
    compile_time_max_seconds = Column(Integer, nullable=True)
    viewport_fps_min = Column(Integer, nullable=True)
    render_time_max_seconds = Column(Integer, nullable=True)
    app_launch_max_seconds = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User")
    test_results = relationship("TestResult", back_populates="standard")


class TestTask(Base):
    """Test task model"""
    __tablename__ = "test_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False)  # benchmark, simulation, full, custom
    task_status = Column(String(20), default="pending", index=True)  # pending, running, completed, failed, cancelled
    
    # Target Devices
    target_device_ids = Column(ARRAY(UUID), default=[])
    target_departments = Column(ARRAY(String), default=[])
    target_positions = Column(ARRAY(String), default=[])
    
    # Test Configuration
    test_script_id = Column(UUID(as_uuid=True), ForeignKey("test_scripts.id"), nullable=True)
    test_duration_seconds = Column(Integer, nullable=True)
    sample_interval_ms = Column(Integer, default=1000)
    
    # Execution Info
    assigned_agent_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Schedule
    schedule_type = Column(String(20), nullable=True)  # immediate, scheduled, recurring
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    cron_expression = Column(String(100), nullable=True)
    
    # Creator
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="test_tasks")
    script = relationship("TestScript")
    results = relationship("TestResult", back_populates="task")


class TestScript(Base):
    """Test script model"""
    __tablename__ = "test_scripts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    script_name = Column(String(200), nullable=False)
    script_code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Target Positions
    target_positions = Column(ARRAY(String), default=[])
    
    # Script Type
    script_type = Column(String(20), default="operation")  # benchmark, operation, mixed
    
    # Script Content (JSON)
    script_content = Column(JSONB, nullable=False)
    
    # Execution Parameters
    timeout_seconds = Column(Integer, default=3600)
    retry_count = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="test_scripts")


class TestResult(Base):
    """Test result model"""
    __tablename__ = "test_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("test_tasks.id"), nullable=True, index=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=True, index=True)
    
    # Test Overview
    test_type = Column(String(50), nullable=True)
    test_status = Column(String(20), nullable=True)  # passed, failed, warning, partial
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    
    # Scores
    overall_score = Column(Float, nullable=True)
    cpu_score = Column(Float, nullable=True)
    gpu_score = Column(Float, nullable=True)
    memory_score = Column(Float, nullable=True)
    disk_score = Column(Float, nullable=True)
    
    # Standard Check
    is_standard_met = Column(Boolean, nullable=True)
    standard_id = Column(UUID(as_uuid=True), ForeignKey("position_standards.id"), nullable=True)
    fail_reasons = Column(JSONB, nullable=True)
    
    # Performance Summary
    performance_summary = Column(JSONB, nullable=True)
    
    # Bottleneck Analysis
    bottleneck_type = Column(String(50), nullable=True)  # CPU, GPU, MEMORY, DISK, NONE
    bottleneck_detail = Column(JSONB, nullable=True)
    
    # Upgrade Suggestion
    upgrade_suggestion = Column(JSONB, nullable=True)
    
    # File Paths
    result_file_path = Column(String(500), nullable=True)
    log_file_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    task = relationship("TestTask", back_populates="results")
    device = relationship("Device", back_populates="test_results")
    standard = relationship("PositionStandard", back_populates="test_results")


class AuditLog(Base):
    """Audit log model for security tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class SystemConfig(Base):
    """System configuration model"""
    __tablename__ = "system_config"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(JSONB, nullable=False)
    config_type = Column(String(20), default="string")
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

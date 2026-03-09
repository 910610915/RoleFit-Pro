"""
PostgreSQL + TimescaleDB 数据库初始化脚本

使用说明:
1. 确保已安装 PostgreSQL 16+ 和 TimescaleDB 扩展
2. 创建数据库: CREATE DATABASE hardware_benchmark;
3. 启用 TimescaleDB: CREATE EXTENSION IF NOT EXISTS timescaledb;
4. 运行此脚本创建表和超表
"""

import psycopg2
from psycopg2 import sql
import os

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "postgres",
    "password": "postgres",
    "database": "hardware_benchmark",
}


def create_tables(conn):
    """创建所有业务表（普通 PostgreSQL 表）"""
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE,
            full_name VARCHAR(100),
            role VARCHAR(20) DEFAULT 'user',
            role_id UUID,
            department_id UUID,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 角色表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(50) UNIQUE NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            is_system BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 设备表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_name VARCHAR(100) NOT NULL,
            mac_address VARCHAR(17) UNIQUE NOT NULL,
            ip_address VARCHAR(15),
            hostname VARCHAR(100),
            
            -- 硬件信息
            cpu_model VARCHAR(200),
            cpu_cores INTEGER,
            cpu_threads INTEGER,
            cpu_base_clock FLOAT,
            
            gpu_model VARCHAR(200),
            gpu_vram_mb INTEGER,
            gpu_driver_version VARCHAR(50),
            all_gpus TEXT,
            
            ram_total_gb FLOAT,
            ram_frequency INTEGER,
            all_memory TEXT,
            
            disk_model VARCHAR(200),
            disk_capacity_tb FLOAT,
            
            -- 归属信息
            department_id VARCHAR(36),
            cost_center VARCHAR(50),
            assigned_user VARCHAR(100),
            position VARCHAR(50),
            location VARCHAR(200),
            purchase_date DATE,
            warranty_expiry DATE,
            purchase_price DECIMAL(10,2),
            supplier VARCHAR(200),
            serial_number VARCHAR(100),
            asset_tag VARCHAR(50),
            
            -- 使用信息
            total_usage_hours DECIMAL(10,2) DEFAULT 0,
            last_used_at TIMESTAMPTZ,
            usage_frequency INTEGER DEFAULT 0,
            
            -- 状态
            status VARCHAR(20) DEFAULT 'online',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            
            owner_id UUID REFERENCES users(id)
        );
    """)

    # 创建索引
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_devices_owner ON devices(owner_id);")

    conn.commit()
    print("✓ 基础表创建完成")


def create_performance_metrics_hypertable(conn):
    """创建性能指标表（TimescaleDB 超表）"""
    cursor = conn.cursor()

    # 先创建普通表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id SERIAL,
            device_id UUID NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            
            -- CPU
            cpu_percent FLOAT,
            cpu_temperature FLOAT,
            cpu_power_watts FLOAT,
            cpu_frequency_mhz FLOAT,
            
            -- GPU
            gpu_percent FLOAT,
            gpu_temperature FLOAT,
            gpu_power_watts FLOAT,
            gpu_frequency_mhz FLOAT,
            gpu_memory_used_mb FLOAT,
            gpu_memory_total_mb FLOAT,
            
            -- 内存
            memory_percent FLOAT,
            memory_used_mb FLOAT,
            memory_available_mb FLOAT,
            
            -- 磁盘
            disk_read_mbps FLOAT,
            disk_write_mbps FLOAT,
            disk_io_percent FLOAT,
            
            -- 网络
            network_sent_mbps FLOAT,
            network_recv_mbps FLOAT,
            
            -- 进程
            process_count INTEGER,
            top_processes JSON,
            
            -- 原始数据
            raw_data JSONB,
            disk_io_details JSONB,
            
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 转换为 TimescaleDB 超表
    cursor.execute("""
        SELECT create_hypertable(
            'performance_metrics', 
            'timestamp',
            if_not_exists => TRUE,
            migrate_data => TRUE
        );
    """)

    # 创建索引
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_perf_device_time ON performance_metrics(device_id, timestamp DESC);"
    )

    # 启用压缩（可选，提高存储效率）
    cursor.execute("""
        ALTER TABLE performance_metrics SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'device_id'
        );
    """)

    # 添加压缩策略（保留30天数据）
    cursor.execute("""
        SELECT add_compression_policy(
            'performance_metrics',
            INTERVAL '30 days',
            if_not_exists => TRUE
        );
    """)

    conn.commit()
    print("✓ TimescaleDB 超表创建完成")


def create_other_tables(conn):
    """创建其他业务表"""
    cursor = conn.cursor()

    # 岗位表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            department VARCHAR(100),
            description TEXT,
            requirements JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 测试软件表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_software (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(200) NOT NULL,
            version VARCHAR(50),
            vendor VARCHAR(100),
            category VARCHAR(50),
            download_url TEXT,
            installed_path TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_tasks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            task_name VARCHAR(200) NOT NULL,
            task_type VARCHAR(50) NOT NULL,
            task_status VARCHAR(20) DEFAULT 'pending',
            
            target_device_ids TEXT DEFAULT '[]',
            target_departments TEXT DEFAULT '[]',
            target_positions TEXT DEFAULT '[]',
            
            test_script_id UUID,
            test_duration_seconds INTEGER,
            sample_interval_ms INTEGER DEFAULT 1000,
            
            assigned_agent_id VARCHAR(100),
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            
            schedule_type VARCHAR(20),
            scheduled_at TIMESTAMPTZ,
            cron_expression VARCHAR(100),
            
            created_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 告警表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            device_id UUID REFERENCES devices(id),
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT,
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            resolved_by UUID REFERENCES users(id),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(36),
            details JSONB,
            ip_address VARCHAR(45),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 第三方API配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS third_party_apis (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            api_type VARCHAR(50) NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            secret TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            headers JSONB,
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    conn.commit()
    print("✓ 其他业务表创建完成")


def main():
    print("=" * 50)
    print("PostgreSQL + TimescaleDB 数据库初始化")
    print("=" * 50)

    try:
        # 连接数据库
        print(f"\n连接到 {DB_CONFIG['database']}...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✓ 连接成功")

        # 启用 TimescaleDB 扩展
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
        conn.commit()
        print("✓ TimescaleDB 扩展已启用")

        # 创建表
        print("\n创建业务表...")
        create_tables(conn)

        print("\n创建性能指标超表...")
        create_performance_metrics_hypertable(conn)

        print("\n创建其他业务表...")
        create_other_tables(conn)

        print("\n" + "=" * 50)
        print("✓ 数据库初始化完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()

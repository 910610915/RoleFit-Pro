"""
MySQL 数据库初始化脚本

使用说明:
1. 确保 MySQL 已安装并运行
2. 运行此脚本创建所有表
"""

import pymysql

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "hardware_benchmark",
    "charset": "utf8mb4",
}


def create_tables(conn):
    """创建所有业务表"""
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id CHAR(36) PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE,
            full_name VARCHAR(100),
            role VARCHAR(20) DEFAULT 'user',
            role_id CHAR(36),
            department_id CHAR(36),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 角色表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id CHAR(36) PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            permissions TEXT,
            is_system BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 设备表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id CHAR(36) PRIMARY KEY,
            device_name VARCHAR(100) NOT NULL,
            mac_address VARCHAR(17) UNIQUE NOT NULL,
            ip_address VARCHAR(15),
            hostname VARCHAR(100),
            
            -- 硬件信息
            cpu_model VARCHAR(200),
            cpu_cores INT,
            cpu_threads INT,
            cpu_base_clock FLOAT,
            
            gpu_model VARCHAR(200),
            gpu_vram_mb INT,
            gpu_driver_version VARCHAR(50),
            all_gpus TEXT,
            
            ram_total_gb FLOAT,
            ram_frequency INT,
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
            last_used_at TIMESTAMP NULL,
            usage_frequency INT DEFAULT 0,
            
            -- 状态
            status VARCHAR(20) DEFAULT 'online',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            owner_id CHAR(36),
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 创建索引
    cursor.execute("CREATE INDEX idx_devices_mac ON devices(mac_address);")
    cursor.execute("CREATE INDEX idx_devices_status ON devices(status);")
    cursor.execute("CREATE INDEX idx_devices_owner ON devices(owner_id);")

    conn.commit()
    print("✓ 基础表创建完成")


def create_performance_metrics_table(conn):
    """创建性能指标表（MySQL 普通表，时序功能有限）"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_id CHAR(36) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            
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
            process_count INT,
            top_processes JSON,
            
            -- 原始数据
            raw_data JSON,
            disk_io_details JSON,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_device_time (device_id, timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    print("✓ 性能指标表创建完成")


def create_other_tables(conn):
    """创建其他业务表"""
    cursor = conn.cursor()

    # 岗位表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id CHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(50) UNIQUE NOT NULL,
            department VARCHAR(100),
            description TEXT,
            requirements JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 测试软件表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_software (
            id CHAR(36) PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            version VARCHAR(50),
            vendor VARCHAR(100),
            category VARCHAR(50),
            download_url TEXT,
            installed_path TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_tasks (
            id CHAR(36) PRIMARY KEY,
            task_name VARCHAR(200) NOT NULL,
            task_type VARCHAR(50) NOT NULL,
            task_status VARCHAR(20) DEFAULT 'pending',
            
            target_device_ids TEXT DEFAULT '[]',
            target_departments TEXT DEFAULT '[]',
            target_positions TEXT DEFAULT '[]',
            
            test_script_id CHAR(36),
            test_duration_seconds INT,
            sample_interval_ms INT DEFAULT 1000,
            
            assigned_agent_id VARCHAR(100),
            started_at TIMESTAMP NULL,
            completed_at TIMESTAMP NULL,
            
            schedule_type VARCHAR(20),
            scheduled_at TIMESTAMP NULL,
            cron_expression VARCHAR(100),
            
            created_by CHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 告警表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alarms (
            id CHAR(36) PRIMARY KEY,
            device_id CHAR(36),
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            message TEXT,
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMP NULL,
            resolved_by CHAR(36),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 审计日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id CHAR(36) PRIMARY KEY,
            user_id CHAR(36),
            action VARCHAR(50) NOT NULL,
            resource_type VARCHAR(50),
            resource_id VARCHAR(36),
            details JSON,
            ip_address VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 第三方API配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS third_party_apis (
            id CHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            api_type VARCHAR(50) NOT NULL,
            base_url TEXT NOT NULL,
            api_key TEXT,
            secret TEXT,
            enabled BOOLEAN DEFAULT TRUE,
            headers JSON,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 测试结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_results (
            id CHAR(36) PRIMARY KEY,
            task_id CHAR(36),
            device_id CHAR(36),
            test_type VARCHAR(50),
            test_status VARCHAR(20),
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration_seconds INT NOT NULL,
            overall_score FLOAT,
            cpu_score FLOAT,
            gpu_score FLOAT,
            memory_score FLOAT,
            disk_score FLOAT,
            is_standard_met BOOLEAN,
            standard_id CHAR(36),
            fail_reasons TEXT,
            performance_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (task_id) REFERENCES test_tasks(id) ON DELETE SET NULL,
            FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    print("✓ 其他业务表创建完成")


def main():
    print("=" * 50)
    print("MySQL 数据库初始化")
    print("=" * 50)

    try:
        # 连接数据库
        print(f"\n连接到 {DB_CONFIG['database']}...")
        conn = pymysql.connect(**DB_CONFIG)
        print("✓ 连接成功")

        # 创建表
        print("\n创建业务表...")
        create_tables(conn)

        print("\n创建性能指标表...")
        create_performance_metrics_table(conn)

        print("\n创建其他业务表...")
        create_other_tables(conn)

        print("\n" + "=" * 50)
        print("✓ 数据库初始化完成!")
        print("=" * 50)
        print("\n现在修改 .env 文件配置数据库类型为 mysql:")
        print("  database_type=mysql")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        raise
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()

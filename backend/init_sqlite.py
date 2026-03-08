"""
SQLite数据库初始化脚本 - 简化版
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.sqlite import (
    Base,
    User,
    Position,
    TestSoftware,
    JobScript,
    ScriptExecution,
    SoftwareMetrics,
    PerformanceMetric,
    SoftwareBenchmark,
    ControlCommand,
    PerformanceAlert,
    AIAnalysisReport,
    Device,
    TestTask,
    TestScript,
    TestResult,
    AlarmRule,
    Alarm,
    AuditLog,
    PositionStandard,
    FeatureCard,
)


def init_database():
    """初始化SQLite数据库"""

    db_path = os.path.join(os.path.dirname(__file__), "hardware_benchmark.db")
    database_url = f"sqlite:///{db_path}"

    print(f"数据库路径: {db_path}")

    # 创建引擎
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    # 创建所有表
    print("正在创建数据库表...")
    Base.metadata.create_all(engine)
    print("✓ 表创建完成")

    # 创建第三方API配置表（如果不存在）
    with engine.connect() as conn:
        result = conn.execute(
            text("""
            SELECT name FROM sqlite_master WHERE type='table' AND name='third_party_apis'
        """)
        )
        if not result.fetchone():
            conn.execute(
                text("""
                CREATE TABLE third_party_apis (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    api_type TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    api_key TEXT,
                    secret TEXT,
                    enabled INTEGER DEFAULT 1,
                    headers TEXT,
                    description TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            )
            conn.commit()
            print("✓ third_party_apis 表创建完成")

    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()

    # 直接使用简单密码哈希（开发环境用）
    admin = session.query(User).filter(User.username == "admin").first()

    if not admin:
        print("正在创建管理员账号...")
        # admin123的bcrypt哈希
        admin = User(
            username="admin",
            email="admin@example.com",
            full_name="系统管理员",
            password_hash="$2b$12$nAD41MKaFbfRFgSfkFuhZOV9XSp1oiTzxFnay8n/ss79xu18AI7pK",
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        print("✓ 管理员账号创建完成")
        print("  用户名: admin")
        print("  密码: admin123")
    else:
        print("✓ 管理员账号已存在")

    session.close()
    print("\n数据库初始化完成！")
    return db_path


if __name__ == "__main__":
    init_database()

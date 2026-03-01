from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import ConfigDict
import os


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"  # Allow extra fields in .env
    )
    
    # Application
    app_name: str = "HardwareBenchmark"
    debug: bool = True
    
    # Database (SQLite)
    database_url: str = "sqlite+aiosqlite:///./hardware_benchmark.db"
    database_url_sync: str = "sqlite:///./hardware_benchmark.db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: list = ["http://localhost:5173", "http://localhost:80"]
    
    # Agent
    agent_heartbeat_interval: int = 30
    agent_data_upload_interval: int = 5
    
    # Benchmark
    benchmark_default_timeout: int = 3600
    benchmark_sample_interval: int = 1000
    
    # Software Storage
    software_storage_path: str = "software"
    
    # ================================================
    # LLM Configuration (多 AI 提供商)
    # ================================================
    # 当前使用的 AI 提供商: siliconflow/minimax/deepseek/zhipu/qwen/openai
    llm_provider: str = "siliconflow"
    
    # API Key (用于 AI 提供商认证)
    llm_api_key: str = ""
    
    # 默认模型 (在对应提供商处配置)
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    
    # 请求超时时间 (秒)
    llm_timeout: int = 60
    
    # 备用提供商配置 (当主提供商失败时自动切换)
    llm_backup_provider: Optional[str] = None
    llm_backup_api_key: Optional[str] = None


settings = Settings()

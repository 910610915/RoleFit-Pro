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
    
    # Database
    database_url: str = "postgresql+asyncpg://benchmark:benchmark@postgres:5432/benchmark_db"
    database_url_sync: str = "postgresql://benchmark:benchmark@postgres:5432/benchmark_db"
    
    # Redis
    redis_url: Optional[str] = None
    
    # InfluxDB
    influxdb_url: Optional[str] = None
    influxdb_token: Optional[str] = None
    influxdb_org: Optional[str] = None
    influxdb_bucket: Optional[str] = None
    
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


settings = Settings()

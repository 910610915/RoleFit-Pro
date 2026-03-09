from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings

# 根据配置选择数据库类型
if settings.database_type == "mysql":
    # MySQL
    database_url = settings.mysql_url_sync
    database_url_async = settings.mysql_url

    # Sync engine for MySQL
    sync_engine = create_engine(
        database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    # Async engine for MySQL
    async_engine = create_async_engine(
        database_url_async,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

elif settings.database_type == "postgresql":
    # PostgreSQL + TimescaleDB
    database_url = settings.postgresql_url_sync
    database_url_async = settings.postgresql_url

    # Sync engine for PostgreSQL
    sync_engine = create_engine(
        database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

    # Async engine for PostgreSQL
    async_engine = create_async_engine(
        database_url_async,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
else:
    # SQLite (默认开发环境)
    database_url = "sqlite:///./hardware_benchmark.db"
    database_url_async = "sqlite+aiosqlite:///./hardware_benchmark.db"

    # Sync engine for SQLite
    sync_engine = create_engine(
        database_url, echo=settings.debug, connect_args={"check_same_thread": False}
    )

    # Async engine for SQLite
    async_engine = create_async_engine(
        database_url_async,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
    )

# Sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


def get_db_sync():
    """Dependency for getting sync database session"""
    with SyncSessionLocal() as session:
        try:
            yield session
        finally:
            session.close()


# Async dependency for FastAPI
async def get_db():
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Keep both names working - get_db_sync returns sync session, get_db returns async session
# This ensures backward compatibility - use get_db_sync for sync functions, get_db for async

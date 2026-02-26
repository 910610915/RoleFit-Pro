from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Use sync SQLite directly - hardcode for reliability
database_url = "sqlite:///./hardware_benchmark.db"

# Sync engine 
sync_engine = create_engine(
    database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False}
)

# Sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
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


# Keep for compatibility
get_db = get_db_sync

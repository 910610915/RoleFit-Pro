# API routes package
from app.api.auth import router as auth_router
from app.api.devices import router as devices_router
from app.api.tasks import router as tasks_router
from app.api.results import router as results_router
from app.api.stats import router as stats_router
from app.api.positions import router as positions_router
from app.api.software import router as software_router
from app.api.scripts import router as scripts_router
from app.api.executions import router as executions_router
from app.api.agent import router as agent_router
from app.api.llm import router as llm_router
from app.api.llm_config import router as llm_config_router
from app.api.performance import router as performance_router

__all__ = [
    "auth_router",
    "devices_router",
    "tasks_router",
    "results_router",
    "stats_router",
    "positions_router",
    "software_router",
    "scripts_router",
    "executions_router",
    "agent_router",
    "llm_router",
    "llm_config_router",
    "performance_router",
]

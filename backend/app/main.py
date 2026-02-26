from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import async_engine, Base

# Import API routers
from app.api import (
    auth as auth_router,
    devices as devices_router,
    tasks as tasks_router,
    results as results_router,
    stats as stats_router,
    positions as positions_router,
    software as software_router,
    scripts as scripts_router,
    executions as executions_router,
    agent as agent_router,
    alarms as alarms_router
)
from app.api import websocket as websocket_router

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Hardware Performance Benchmark and Position Configuration Analysis System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices_router.router, prefix="/api", tags=["Devices"])
app.include_router(tasks_router.router, prefix="/api", tags=["Tasks"])
app.include_router(results_router.router, prefix="/api", tags=["Results"])
app.include_router(stats_router.router, prefix="/api", tags=["Statistics"])
app.include_router(positions_router.router, prefix="/api", tags=["Positions"])
app.include_router(software_router.router, prefix="/api", tags=["Software"])
app.include_router(scripts_router.router, prefix="/api", tags=["Scripts"])
app.include_router(executions_router.router, prefix="/api", tags=["Executions"])
app.include_router(agent_router.router, prefix="/api/agent", tags=["Agent"])
app.include_router(alarms_router.router, prefix="/api", tags=["Alarms"])
app.include_router(websocket_router.router, tags=["WebSocket"])


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await async_engine.dispose()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to HardwareBenchmark API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

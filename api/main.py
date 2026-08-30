"""
FastAPI main application entry point.

Sets up the FastAPI application with:
- CORS middleware configuration
- Router registration for all API endpoints
- Database lifecycle management (startup/shutdown)
- Health check and root info endpoints
- Logging configuration

Requirements: 6.1
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import benchmark_router, formulas_router, verification_router
from services.database import get_database_service

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database connection pool
    - Shutdown: Close database connection pool
    """
    # Startup
    logger.info("Starting Formula Benchmark API...")
    db_service = get_database_service()
    try:
        await db_service.startup()
        logger.info("Database connection pool initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Formula Benchmark API...")
    try:
        await db_service.shutdown()
        logger.info("Database connection pool closed successfully")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
## Formula Benchmark API

API for comparing dynamic formula calculation methods across different programming languages.

### Features
- **Benchmark Results**: View execution times for all formulas across calculation methods
- **Method Comparison**: Compare overall performance between .NET, Python, and SQL engines
- **Result Verification**: Verify that all methods produce identical results
- **Formula Management**: Browse and inspect formula definitions

### Calculation Methods
- **DotNet_DataTable**: .NET DataTable.Compute engine
- **Python_Eval**: Python eval() with safe AST parsing
- **SQL_Dynamic**: PostgreSQL dynamic SQL stored procedures
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Register routers
app.include_router(benchmark_router)
app.include_router(formulas_router)
app.include_router(verification_router)


@app.get("/", tags=["root"])
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.
    
    Returns basic information about the API including
    name, version, description, and available endpoints.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "API for comparing dynamic formula calculation methods",
        "documentation": "/docs",
        "endpoints": {
            "benchmark_results": "/api/benchmark/results",
            "benchmark_comparison": "/api/benchmark/comparison",
            "formulas": "/api/formulas",
            "verify_results": "/api/results/verify",
            "health": "/health",
        },
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.
    
    Returns the health status of the API and its dependencies.
    Checks database connectivity and returns detailed status.
    """
    db_service = get_database_service()
    
    try:
        db_healthy = await db_service.check_connection()
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        db_healthy = False
    
    overall_status = "healthy" if db_healthy else "degraded"
    
    return {
        "status": overall_status,
        "version": settings.app_version,
        "checks": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connection": "connected" if db_healthy else "disconnected",
            },
        },
    }


# Entry point for running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

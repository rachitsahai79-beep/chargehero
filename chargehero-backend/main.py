"""ChargeHero Backend API - Main application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse
from config import settings
from shared.database import get_db_instance, get_db
from domains.auth.routes import router as auth_router
from domains.jobs.routes import router as jobs_router
from domains.jobs.checklist_routes import router as checklist_router
from domains.jobs.service_report_routes import router as service_report_router
from domains.copilot.copilot_routes import router as copilot_router

# Configure logging
logging.basicConfig(
    level=logging.getLevelName(settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting ChargeHero Backend API")
    db = get_db_instance()
    if db:
        is_healthy = db.health_check()
        if is_healthy:
            logger.info("Database connection established")
        else:
            logger.warning("Database health check failed at startup")
    else:
        logger.warning("Failed to initialize database at startup")

    yield

    # Shutdown
    logger.info("Shutting down ChargeHero Backend API")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="ChargeHero - Enterprise EV Charging Ticketing System Backend API",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZIP middleware (should be last/outermost)
app.add_middleware(GZIPMiddleware, minimum_size=1000)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(checklist_router, prefix="/api/v1/jobs", tags=["checklists"])
app.include_router(service_report_router, prefix="/api/v1/jobs", tags=["service-reports"])
app.include_router(copilot_router, prefix="/api/v1", tags=["copilot"])


# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check(db = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint to verify API and database connectivity.
    Returns 503 Service Unavailable if database is unhealthy.

    Returns:
        dict: Health status information
    """
    try:
        db_healthy = db.health_check()

        if db_healthy:
            return {
                "status": "ok",
                "environment": settings.environment,
                "version": settings.api_version
            }
        else:
            # Return 503 when database is unavailable
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "environment": settings.environment,
                    "error": "Database connectivity issue"
                }
            )
    except Exception as e:
        # Log full error, return generic message to client
        logger.error(f"Health check error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Health check failed"
            }
        )


# Root endpoint
@app.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.

    Returns:
        dict: API information and available endpoints
    """
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )

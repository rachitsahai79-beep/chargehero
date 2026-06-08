"""ChargeHero Backend API - Main application entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from shared.database import db

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
    is_healthy = await db.health_check()
    if is_healthy:
        logger.info("Database connection established")
    else:
        logger.warning("Database health check failed at startup")

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


# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.

    Returns:
        dict: Health status information
    """
    try:
        db_healthy = await db.health_check()
        return {
            "status": "healthy" if db_healthy else "degraded",
            "service": "ChargeHero Backend API",
            "version": settings.api_version,
            "database": "connected" if db_healthy else "disconnected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "ChargeHero Backend API",
            "version": settings.api_version,
            "database": "error",
            "error": str(e),
        }


# Root endpoint
@app.get("/")
async def root():
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

"""
FastAPI main application file.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for ASX Announcements SaaS application",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs" if settings.is_development else "disabled",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    from datetime import datetime
    from app.db.session import engine

    # Check database connection
    database_status = "connected"
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception:
        database_status = "disconnected"

    status = "healthy" if database_status == "connected" else "degraded"

    return JSONResponse(
        status_code=200 if status == "healthy" else 503,
        content={
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version,
            "environment": settings.environment,
            "database": database_status,
        },
    )


# Import and include API routers
from app.api.routes import announcements, companies

app.include_router(
    announcements.router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    companies.router,
    prefix=settings.api_v1_prefix,
)

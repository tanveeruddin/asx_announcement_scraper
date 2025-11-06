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
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
        },
    )


# API routes will be added here as we build them
# Example:
# from app.api.v1 import announcements, auth, companies
# app.include_router(announcements.router, prefix=f"{settings.api_v1_prefix}/announcements")
# app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth")
# app.include_router(companies.router, prefix=f"{settings.api_v1_prefix}/companies")

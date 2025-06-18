"""
Main FastAPI application.
Configures the app with authentication, CORS, logging, and error handling.
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.routers import auth, content


# Configure logging
def configure_logging():
    """Configure structured logging with Loguru."""
    # Remove default handler
    logger.remove()

    # Add structured logging
    if settings.log_format == "json":
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        )

    # Add file logging for production
    if settings.environment == "production":
        logger.add(
            "logs/app.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            serialize=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Promptly API...")
    configure_logging()

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down...")
        await close_db()
        logger.info("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Promptly - AI-powered professional social media content creation platform",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed messages."""
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")

    # Clean up error details to make them JSON serializable
    cleaned_errors = []
    for error in exc.errors():
        cleaned_error = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        # Remove ctx field or clean it up if it contains non-serializable objects
        if "ctx" in error and error["ctx"]:
            # Convert any non-serializable objects to strings
            cleaned_ctx = {}
            for key, value in error["ctx"].items():
                if isinstance(value, Exception):
                    cleaned_ctx[key] = str(value)
                else:
                    cleaned_ctx[key] = value
            cleaned_error["ctx"] = cleaned_ctx
        cleaned_errors.append(cleaned_error)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "The request data is invalid",
            "details": cleaned_errors,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with appropriate logging."""
    logger.error(f"Unhandled exception on {request.url}: {exc}")

    # Don't expose internal errors in production
    if settings.environment == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for audit purposes."""
    # start_time = logger.bind(time=True)

    # Get client IP (handle reverse proxy headers)
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip", "")
        or request.client.host
        if request.client
        else "unknown"
    )

    # Special logging for OPTIONS requests that are failing
    if request.method == "OPTIONS" and "signin/google" in str(request.url):
        headers_dict = dict(request.headers)
        logger.info(
            "OPTIONS request headers for signin/google",
            extra={
                "method": request.method,
                "url": str(request.url),
                "headers": headers_dict,
            },
        )

    # Log request
    logger.info(
        f"Request: {request.method} {request.url} from {client_ip}",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
        },
    )

    # Process request
    response = await call_next(request)

    # Log response
    logger.info(
        f"Response: {response.status_code} for {request.method} {request.url}",
        extra={
            "status_code": response.status_code,
            "method": request.method,
            "url": str(request.url),
        },
    )

    return response


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else "disabled",
    }


# CORS preflight handler
@app.options("/{path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests for CORS preflight."""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*"
            if settings.environment == "development"
            else request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,PATCH,OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "600",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": "2024-01-01T00:00:00Z",
    }


# Metrics endpoint (basic implementation)
# In a production environment, integrate with Prometheus or similar
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "up",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=False,  # We handle logging in middleware
    )

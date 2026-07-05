"""
FastAPI Main Application for Fraud Detection Platform
"""
import os
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.routes import auth, transactions, scoring, models, alerts, reports
from api.middleware.auth import AuthService
from api.database import get_supabase_client

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Fraud Detection Platform API")
    # Initialize connections
    app.state.supabase = get_supabase_client()
    app.state.auth_service = AuthService()
    yield
    logger.info("Shutting down Fraud Detection Platform API")

# Create FastAPI app
app = FastAPI(
    title="AI Financial Fraud Detection API",
    description="""
    Production-ready fraud detection platform with ML-powered scoring,
    explainable AI (SHAP), and real-time anomaly detection.

    ## Features

    * **Real-time Scoring** - Sub-100ms fraud risk assessment
    * **Explainable AI** - SHAP values for every prediction
    * **Model Management** - Train, compare, and deploy ML models
    * **Anomaly Detection** - Isolation Forest, LOF, Autoencoder
    * **RBAC** - Role-based access (Analyst, Manager, Admin)

    ## Authentication

    Use Bearer token authentication. Obtain tokens via `/auth/login`.
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://fraud-detection.vercel.app").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Client-Info"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transactions"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["Scoring"])
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error("Validation error", errors=exc.errors(), path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": "An unexpected error occurred"}
    )

# Health check endpoint
@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "fraud-detection-api"}

# API info endpoint
@app.get("/api/v1", tags=["API Info"])
async def api_info():
    return {
        "name": "AI Financial Fraud Detection API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "transactions": "/api/v1/transactions",
            "scoring": "/api/v1/scoring",
            "models": "/api/v1/models",
            "alerts": "/api/v1/alerts",
            "reports": "/api/v1/reports"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )

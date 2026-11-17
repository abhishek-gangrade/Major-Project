import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.routes import (
    auth,
    questions,
    practice,
    progress,
    recommendations,
    research,
    admin,
)

app = FastAPI(
    title=f"{settings.PROJECT_NAME} API",
    description=(
        "AdaptivePrep: A Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation. "
        "Final-year B.Tech CSE Major Project, Medi-Caps University, Indore. "
        "Project Team: Abhishek Gangrade, Aastha Jain. Project Guide: Prof. HarshPratap Singh."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_and_timing_headers(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Centralized safe error handling: prevents internal stack traces from leaking."""
    # In development or test, error details can be inspected, but avoid leaking DB internals to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Health check
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "algorithm_version": settings.ALGORITHM_VERSION,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to AdaptivePrep API — Personalized Placement Preparation Platform",
        "institution": "Medi-Caps University, Indore",
        "team": ["Abhishek Gangrade", "Aastha Jain"],
        "guide": "Prof. HarshPratap Singh",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


# Include versioned API routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(practice.router, prefix=settings.API_V1_STR)
app.include_router(progress.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(research.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)


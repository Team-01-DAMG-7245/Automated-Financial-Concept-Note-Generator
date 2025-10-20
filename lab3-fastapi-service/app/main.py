"""
Main FastAPI application entry point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import query, seed
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting AURELIA FastAPI RAG Service...")
    logger.info(f"Environment: {settings.environment}")
    yield
    # Shutdown
    logger.info("Shutting down AURELIA FastAPI RAG Service...")


# Create FastAPI application
app = FastAPI(
    title="AURELIA RAG Service",
    description="Retrieval-Augmented Generation service for Financial Concept Notes",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(seed.router, prefix="/api/v1", tags=["seed"])


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "AURELIA RAG Service",
        "version": "1.0.0"
    }


@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Welcome to AURELIA RAG Service",
        "docs": "/docs",
        "health": "/health"
    }


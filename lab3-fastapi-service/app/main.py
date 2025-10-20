"""
Main FastAPI application entry point
"""
import logging
from pathlib import Path

# 1) Load .env BEFORE importing anything that reads env vars
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import query, seed
from app.core.config import settings
from app.core.db import Base, engine

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/Shutdown lifecycle
    """
    # Ensure tables exist AFTER env is loaded & engine is built with correct URL
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("DB tables ensured (create_all).")
    except Exception as e:
        logger.exception(f"DB init failed: {e}")
        raise

    logger.info("Starting AURELIA FastAPI RAG Service...")
    logger.info(f"Environment: {settings.environment}")
    yield
    logger.info("Shutting down AURELIA FastAPI RAG Service...")


# 2) Single app instance
app = FastAPI(
    title="AURELIA RAG Service",
    description="Retrieval-Augmented Generation service for Financial Concept Notes",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 3) CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4) Routers (register once with a versioned prefix)
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(seed.router,  prefix="/api/v1", tags=["seed"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy", "service": "AURELIA RAG Service", "version": "1.0.0"}


@app.get("/", tags=["root"])
async def root():
    return {"message": "Welcome to AURELIA RAG Service", "docs": "/docs", "health": "/health"}

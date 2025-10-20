"""
Database setup and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings  # optional, if you want to read from .env through Settings

# Prefer DATABASE_URL in your .env
DATABASE_URL = os.getenv("DATABASE_URL") or f"postgresql+psycopg://user:pass@localhost:5432/aurelia_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()



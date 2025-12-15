"""
Database connection management for Supabase PostgreSQL.

This module handles all database connectivity, session management,
and provides utilities for health checks.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Load environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Supabase connection string from environment
# Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise EnvironmentError(
        "DATABASE_URL environment variable is required. "
        "Set it to your Supabase PostgreSQL connection string."
    )

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set True for SQL debugging
    poolclass=QueuePool,
    pool_pre_ping=True,  # Handle connection drops gracefully
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,  # Recycle connections after 5 minutes
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Provides automatic commit on success and rollback on failure.
    
    Usage:
        with get_session() as session:
            result = session.query(Model).all()
            session.add(new_object)
            # Commits automatically on exit
    
    Yields:
        SQLAlchemy Session object
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """
    Initialize database schema.
    
    Creates all tables defined in models.py if they don't exist.
    Safe to call multiple times.
    """
    from storage.models import Base
    Base.metadata.create_all(engine)
    print("✅ Database schema initialized successfully")


def check_connection() -> bool:
    """
    Verify database connectivity.
    
    Returns:
        True if connection successful, False otherwise.
        
    Used for health checks and dashboard status display.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Retrieve database connection information for diagnostics.
    
    Returns:
        Dict with connection status and metadata
    """
    info = {
        "connected": False,
        "database": None,
        "host": None,
        "pool_size": engine.pool.size(),
    }
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT current_database(), inet_server_addr()"))
            row = result.fetchone()
            info["connected"] = True
            info["database"] = row[0] if row else None
            info["host"] = str(row[1]) if row and row[1] else "localhost"
    except Exception as e:
        info["error"] = str(e)
    
    return info

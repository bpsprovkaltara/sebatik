from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import DEFAULT_DB_PATH, settings
from .db.base import Base

# Nama lama dipertahankan untuk skrip yang masih menunjuk berkas SQLite arsip.
DEFAULT_DB: Path = DEFAULT_DB_PATH
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.is_sqlite else {},
    # Koneksi yang menganggur lama diputus PostgreSQL; pre_ping memastikan
    # sesi berikutnya tidak memakai koneksi mati.
    pool_pre_ping=not settings.is_sqlite,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Alias lama untuk `deps.get_session`; dipertahankan agar skrip tetap jalan."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["Base", "DATABASE_URL", "DEFAULT_DB", "SessionLocal", "engine", "get_db"]

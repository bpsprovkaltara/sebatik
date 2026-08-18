from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import DEFAULT_DB_PATH, settings
from .db.base import Base

# Dipertahankan sebagai nama lama agar modul yang belum dipindahkan tetap jalan.
DEFAULT_DB: Path = DEFAULT_DB_PATH
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.is_sqlite else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# Keep existing installations forward-compatible without deleting imported data.
# TODO(fase 2): dihapus setelah skema dikelola Alembic sepenuhnya.
if DEFAULT_DB.exists() and settings.sqlite_path == DEFAULT_DB:
    from src.etl.features import migrate_governance

    migrate_governance(DEFAULT_DB)
    from .master_seed import seed_verified_master

    seed_verified_master(DEFAULT_DB)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


__all__ = ["Base", "DATABASE_URL", "DEFAULT_DB", "SessionLocal", "engine", "get_db"]

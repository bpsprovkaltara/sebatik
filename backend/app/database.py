from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "processed" / "sebatik.db"
DATABASE_URL = os.getenv("SEBATIK_DATABASE_URL", f"sqlite:///{DEFAULT_DB.as_posix()}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


# Keep existing installations forward-compatible without deleting imported data.
if DEFAULT_DB.exists() and DATABASE_URL == f"sqlite:///{DEFAULT_DB.as_posix()}":
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

"""Konfigurasi bersama pytest.

`tmp_path` bawaan menulis ke `%TEMP%\\pytest-of-<user>` yang pada sebagian mesin
Windows tidak dapat dibuat (akses ditolak). Mengarahkan akar direktori sementara
ke `tmp/` di dalam repo membuat tes ETL dapat berjalan di mana pun.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = REPO_ROOT / "tmp" / "pytest"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(TEMP_ROOT))

# Dipasang tanpa `setdefault`: nilai dari `.env` harus benar-benar dikalahkan.
# Basis data tidak ikut dipaku karena tiap fixture menyiapkannya sendiri.
os.environ["SEBATIK_ENVIRONMENT"] = "test"
os.environ["SEBATIK_SECRET_KEY"] = "kunci-uji-yang-panjangnya-lebih-dari-32-karakter"
os.environ["SEBATIK_SECRET_KEYS"] = ""
os.environ["SEBATIK_DATABASE_URL"] = f"sqlite:///{(TEMP_ROOT / 'bawaan.db').as_posix()}"


@pytest.fixture(scope="session")
def engine_uji(tmp_path_factory: pytest.TempPathFactory):
    """Basis data uji yang skemanya dibangun Alembic, bukan `create_all`.

    Memakai Alembic memastikan migrasi yang dipakai produksi ikut teruji; kalau
    skema dibangun langsung dari model, migrasi yang rusak tidak akan ketahuan.
    """
    from alembic import command
    from alembic.config import Config

    berkas = tmp_path_factory.mktemp("db") / "sebatik-uji.db"
    url = f"sqlite:///{berkas.as_posix()}"

    config = Config(str(REPO_ROOT / "backend" / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "backend" / "alembic"))
    config.set_main_option("sqlalchemy.url", url)
    lama = os.environ.get("SEBATIK_DATABASE_URL")
    os.environ["SEBATIK_DATABASE_URL"] = url
    try:
        command.upgrade(config, "head")
    finally:
        if lama is None:
            os.environ.pop("SEBATIK_DATABASE_URL", None)
        else:
            os.environ["SEBATIK_DATABASE_URL"] = lama

    mesin = create_engine(url)

    @event.listens_for(mesin, "connect")
    def _nyalakan_foreign_key(koneksi_dbapi, _catatan):  # pragma: no cover - hook
        """SQLite mengabaikan foreign key kecuali dinyalakan per koneksi."""
        kursor = koneksi_dbapi.cursor()
        kursor.execute("PRAGMA foreign_keys=ON")
        kursor.close()

    yield mesin
    mesin.dispose()


@pytest.fixture
def session(engine_uji) -> Iterator[Session]:
    """Session yang selalu di-rollback, sehingga tes tidak saling mengotori."""
    koneksi = engine_uji.connect()
    transaksi = koneksi.begin()
    pabrik = sessionmaker(bind=koneksi, autoflush=False, autocommit=False)
    sesi = pabrik()
    try:
        yield sesi
    finally:
        sesi.close()
        # Pelanggaran constraint yang sengaja diuji sudah membatalkan transaksi;
        # memanggil rollback dua kali memicu peringatan SQLAlchemy.
        if transaksi.is_active:
            transaksi.rollback()
        koneksi.close()

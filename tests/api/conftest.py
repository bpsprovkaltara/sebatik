"""Fixture aplikasi untuk tes kontrak API.

Aplikasi diuji terhadap basis data yang dibangun **persis seperti produksi**:
skema dari migrasi Alembic, isi dari skrip pemindahan data yang sama. Dengan
begitu tes kontrak menguji jalur yang benar-benar dipakai, bukan skema tiruan.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
SUMBER_SQLITE = REPO_ROOT / "data" / "processed" / "sebatik.db"


@pytest.fixture(scope="session")
def db_termigrasi(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Salinan basis data produksi yang sudah dipindahkan ke skema konsolidasi."""
    if not SUMBER_SQLITE.exists():
        pytest.skip(f"Basis data sumber tidak tersedia: {SUMBER_SQLITE}")

    from scripts.migrasi_ke_skema_target import jalankan

    berkas = tmp_path_factory.mktemp("api") / "sebatik-kontrak.db"
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

    if jalankan(SUMBER_SQLITE, url, kosongkan=False) != 0:
        pytest.fail("Pemindahan data untuk tes kontrak gagal")
    return url


@pytest.fixture(scope="session")
def client(db_termigrasi: str) -> Iterator[TestClient]:
    from backend.app.deps import get_session
    from backend.app.main import create_app

    mesin = create_engine(db_termigrasi)

    @event.listens_for(mesin, "connect")
    def _nyalakan_foreign_key(koneksi_dbapi, _catatan):  # pragma: no cover - hook
        kursor = koneksi_dbapi.cursor()
        kursor.execute("PRAGMA foreign_keys=ON")
        kursor.close()

    pabrik = sessionmaker(bind=mesin, autoflush=False, autocommit=False)

    def sesi_uji():
        sesi = pabrik()
        try:
            yield sesi
        finally:
            sesi.close()

    app = create_app()
    app.dependency_overrides[get_session] = sesi_uji
    # raise_server_exceptions=False supaya galat server terlihat sebagai 500
    # pada tes, sama seperti yang dilihat klien sungguhan.
    with TestClient(app, raise_server_exceptions=False) as klien:
        yield klien
    mesin.dispose()


@pytest.fixture(scope="session")
def auth(client: TestClient) -> dict[str, str]:
    """Header Authorization untuk akun admin seed."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Sebatik-Ganti-Segera-2026!"},
    )
    assert response.status_code == 200, "akun seed admin harus ada untuk tes API"
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

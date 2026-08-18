"""Unit test untuk lapisan konfigurasi terpusat."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.app.config import DEFAULT_DB_PATH, SECRET_BAWAAN, Settings


def test_nilai_bawaan_sama_dengan_perilaku_lama():
    """Fase 0 tidak boleh mengubah perilaku: bawaan harus identik dengan sebelumnya."""
    settings = Settings(_env_file=None)
    assert settings.database_url == f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    assert settings.secret_key == SECRET_BAWAAN
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert settings.access_token_ttl_hours == 8
    assert settings.kode_provinsi == "65"
    assert settings.max_bukti_bytes == 10 * 1024 * 1024
    assert settings.max_unggah_bytes == 30 * 1024 * 1024
    assert settings.archive_dir == DEFAULT_DB_PATH.parent / "arsip-unggahan"
    assert settings.evidence_dir == DEFAULT_DB_PATH.parent / "bukti-dukung"


def test_membaca_variabel_lingkungan_berawalan_sebatik(monkeypatch):
    monkeypatch.setenv("SEBATIK_DATABASE_URL", "postgresql+psycopg://u:p@localhost:5432/sebatik")
    monkeypatch.setenv("SEBATIK_SECRET_KEY", "x" * 40)
    monkeypatch.setenv("SEBATIK_ARCHIVE_DIR", "/data/arsip")
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.is_sqlite is False
    assert settings.sqlite_path is None
    assert settings.archive_dir == Path("/data/arsip")


def test_cors_origins_boleh_dipisah_koma(monkeypatch):
    monkeypatch.setenv("SEBATIK_CORS_ORIGINS", "https://a.go.id, https://b.go.id")
    assert Settings(_env_file=None).cors_origins == ["https://a.go.id", "https://b.go.id"]


def test_sqlite_path_terbaca_dari_url():
    settings = Settings(_env_file=None)
    assert settings.is_sqlite is True
    assert settings.sqlite_path == DEFAULT_DB_PATH


def test_produksi_menolak_secret_bawaan(monkeypatch):
    monkeypatch.setenv("SEBATIK_ENVIRONMENT", "production")
    with pytest.raises(RuntimeError, match="SEBATIK_SECRET_KEY"):
        Settings(_env_file=None).validasi_produksi()


def test_produksi_menolak_secret_pendek(monkeypatch):
    monkeypatch.setenv("SEBATIK_ENVIRONMENT", "production")
    monkeypatch.setenv("SEBATIK_SECRET_KEY", "terlalu-pendek")
    with pytest.raises(RuntimeError):
        Settings(_env_file=None).validasi_produksi()


def test_produksi_menerima_secret_acak_panjang(monkeypatch):
    monkeypatch.setenv("SEBATIK_ENVIRONMENT", "production")
    monkeypatch.setenv("SEBATIK_SECRET_KEY", "z" * 32)
    Settings(_env_file=None).validasi_produksi()


def test_development_tidak_memaksa_secret():
    Settings(_env_file=None).validasi_produksi()

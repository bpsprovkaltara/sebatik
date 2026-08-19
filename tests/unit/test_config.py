"""Unit test untuk lapisan konfigurasi terpusat."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.app.config import DEFAULT_DB_PATH, SECRET_BAWAAN, Settings


@pytest.fixture(autouse=True)
def lingkungan_bersih(monkeypatch: pytest.MonkeyPatch):
    """Buang seluruh variabel SEBATIK_* sebelum tiap tes di berkas ini.

    Tes di sini menguji nilai *bawaan* dan pembacaan variabel tertentu, jadi
    keduanya hanya bermakna bila tidak ada setelan lain yang membayangi — baik
    dari `.env` pengembang maupun dari yang dipasang tests/conftest.py.
    """
    for nama in list(os.environ):
        if nama.startswith("SEBATIK_"):
            monkeypatch.delenv(nama, raising=False)


def test_nilai_bawaan_sama_dengan_perilaku_lama():
    """Bawaan tetap seperti sebelum refactoring, kecuali yang sengaja diubah.

    TTL token adalah pengecualian yang disengaja: auth-keamanan.md §3 Opsi A
    meminta token akses berumur pendek, dengan sesi dipertahankan lewat token
    segar. Diuji terpisah di `test_ttl_token_dipendekkan_dan_ada_token_segar`.
    """
    settings = Settings(_env_file=None)
    assert settings.database_url == f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    assert settings.secret_key == SECRET_BAWAAN
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
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


def test_ttl_token_dipendekkan_dan_ada_token_segar():
    """auth-keamanan.md §3: TTL akses 1-2 jam, sesi disambung token segar."""
    settings = Settings(_env_file=None)
    assert 1 <= settings.access_token_ttl_hours <= 2
    assert settings.refresh_token_ttl_hours > settings.access_token_ttl_hours


def test_kunci_lama_boleh_dipisah_koma(monkeypatch):
    """Rotasi kunci (auth-keamanan.md §2.4) dibaca dari satu baris `.env`."""
    monkeypatch.setenv("SEBATIK_SECRET_KEYS", "kunci-lama-satu, kunci-lama-dua")
    assert Settings(_env_file=None).secret_keys == ["kunci-lama-satu", "kunci-lama-dua"]


def test_tanpa_rotasi_daftar_kunci_lama_kosong():
    assert Settings(_env_file=None).secret_keys == []

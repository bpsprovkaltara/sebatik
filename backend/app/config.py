"""Satu-satunya sumber konfigurasi aplikasi.

Menggantikan `os.getenv` yang tersebar di `main.py`, `database.py`, dan
`features_api.py`. Nama variabel lingkungan (`SEBATIK_*`) sengaja dipertahankan
persis seperti sebelumnya agar berkas `.env` produksi tidak perlu diubah.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "processed" / "sebatik.db"

# Nilai bawaan lama. Aplikasi menolak mulai dengan nilai ini di lingkungan
# produksi (lihat `Settings.validasi_produksi`).
SECRET_BAWAAN = "GANTI-SECRET-INI-SEBELUM-PRODUKSI-SEBATIK"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SEBATIK_",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # `development` melonggarkan kewajiban rahasia; `production` mengetatkannya.
    environment: str = "development"

    database_url: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    secret_key: str = SECRET_BAWAAN
    # Kunci lama yang masih diterima saat memverifikasi token (auth-keamanan.md
    # §2.4). Diisi saat rotasi supaya sesi yang sedang berjalan tidak ditolak
    # serentak; dikosongkan lagi setelah token lama pasti kedaluwarsa.
    secret_keys: Annotated[list[str], NoDecode] = []
    archive_dir: Path = DEFAULT_DB_PATH.parent / "arsip-unggahan"
    evidence_dir: Path = DEFAULT_DB_PATH.parent / "bukti-dukung"
    # NoDecode: nilai env dibaca mentah agar daftar dipisah koma diterima,
    # bukan dipaksa JSON oleh pydantic-settings.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    # Token akses sengaja pendek; sesi dipertahankan lewat token segar
    # httpOnly di `/auth/refresh` (auth-keamanan.md §3 Opsi A).
    access_token_ttl_hours: int = 2
    refresh_token_ttl_hours: int = 24
    kode_provinsi: str = "65"
    max_bukti_bytes: int = 10 * 1024 * 1024
    max_unggah_bytes: int = 30 * 1024 * 1024

    @field_validator("cors_origins", "secret_keys", mode="before")
    @classmethod
    def _pisah_daftar(cls, value: object) -> object:
        """Terima daftar dipisah koma agar `.env` tetap satu baris."""
        if isinstance(value, str) and not value.strip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "produksi"}

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def sqlite_path(self) -> Path | None:
        """Lokasi berkas SQLite, atau None bila memakai basis data lain."""
        if not self.is_sqlite:
            return None
        _, _, sisa = self.database_url.partition("sqlite:///")
        return Path(sisa) if sisa else None

    def validasi_produksi(self) -> None:
        """Dipanggil `create_app`; gagal cepat daripada berjalan tanpa rahasia."""
        if not self.is_production:
            return
        if self.secret_key == SECRET_BAWAAN or len(self.secret_key) < 32:
            raise RuntimeError("SEBATIK_SECRET_KEY wajib diisi acak minimal 32 karakter di produksi.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""Lingkungan migrasi Alembic.

URL basis data dan metadata model dibaca dari aplikasi, bukan diulang di
`alembic.ini`, sehingga migrasi selalu mengikuti konfigurasi yang sama dengan
proses yang melayani API.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.app.config import settings
from backend.app.models import Base  # noqa: F401  (mengisi Base.metadata)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _url() -> str:
    """URL basis data: yang di-set pemanggil lebih dulu, baru settings.

    Pemanggil programatik (tes, skrip migrasi data) sudah menetapkan
    `sqlalchemy.url` pada objek Config. Menimpanya dengan `settings` akan
    membuat migrasi berjalan di basis data yang salah — termasuk basis data
    produksi saat sedang menyiapkan basis data uji.
    """
    return config.get_main_option("sqlalchemy.url") or settings.database_url


DATABASE_URL = _url()
config.set_main_option("sqlalchemy.url", DATABASE_URL.replace("%", "%%"))
target_metadata = Base.metadata
# SQLite tidak mendukung ALTER TABLE penuh; batch mode membuat satu berkas
# migrasi berjalan di SQLite maupun PostgreSQL.
RENDER_AS_BATCH = DATABASE_URL.startswith("sqlite")


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=RENDER_AS_BATCH,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=RENDER_AS_BATCH,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

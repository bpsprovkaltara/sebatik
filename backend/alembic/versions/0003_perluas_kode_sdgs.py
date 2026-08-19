"""Perluas kode SDGs agar uraian dari basis data lama tidak terpotong.

Kolomnya semula `String(40)`, padahal sebagian sumber lama menyimpan uraian
indikator SDGs lengkap — yang terpanjang 634 karakter. SQLite mengabaikan
panjang `VARCHAR` sehingga tidak pernah mengeluh, tetapi PostgreSQL
menegakkannya dan akan menggagalkan pemindahan data saat cutover.

Revision ID: 0003_kode_sdgs_text
Revises: 0002_seed_wilayah
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_kode_sdgs_text"
down_revision = "0002_seed_wilayah"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table wajib di sini: SQLite tidak punya ALTER COLUMN, jadi
    # Alembic membangun ulang tabelnya. `render_as_batch` di env.py hanya
    # memengaruhi hasil autogenerate, bukan operasi yang ditulis tangan.
    with op.batch_alter_table("indikator") as batch:
        batch.alter_column(
            "kode_sdgs",
            existing_type=sa.String(length=40),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Downgrade sengaja dibiarkan gagal bila sudah ada uraian panjang;
    # PostgreSQL tidak boleh memotong data diam-diam saat kembali ke revisi lama.
    with op.batch_alter_table("indikator") as batch:
        batch.alter_column(
            "kode_sdgs",
            existing_type=sa.Text(),
            type_=sa.String(length=40),
            existing_nullable=True,
        )

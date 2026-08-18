"""Seed wilayah Kalimantan Utara.

Enam wilayah ini statis dan menjadi prasyarat foreign key hampir semua tabel
lain (`pengguna.wilayah_kode`, `nilai_indikator.wilayah_kode`,
`usulan_nilai.wilayah_kode`), jadi diisi lewat migrasi data, bukan skrip seed
terpisah yang bisa terlupa dijalankan.

Revision ID: 0002_seed_wilayah
Revises: 0001_baseline
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_seed_wilayah"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


WILAYAH_KALTARA: tuple[tuple[str, str, str, str | None], ...] = (
    ("65", "Kalimantan Utara", "PROVINSI", None),
    ("6501", "Bulungan", "KABUPATEN", "65"),
    ("6502", "Malinau", "KABUPATEN", "65"),
    ("6503", "Nunukan", "KABUPATEN", "65"),
    ("6504", "Tana Tidung", "KABUPATEN", "65"),
    ("6571", "Tarakan", "KOTA", "65"),
)

wilayah = sa.table(
    "wilayah",
    sa.column("kode", sa.String),
    sa.column("nama", sa.String),
    sa.column("tingkat", sa.String),
    sa.column("parent_kode", sa.String),
    sa.column("aktif", sa.Boolean),
)


def upgrade() -> None:
    op.bulk_insert(
        wilayah,
        [
            {"kode": kode, "nama": nama, "tingkat": tingkat, "parent_kode": induk, "aktif": True}
            for kode, nama, tingkat, induk in WILAYAH_KALTARA
        ],
    )


def downgrade() -> None:
    kode_wilayah = [item[0] for item in WILAYAH_KALTARA]
    op.execute(sa.delete(wilayah).where(sa.column("kode").in_(kode_wilayah)))

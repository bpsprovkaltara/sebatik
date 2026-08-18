"""Baseline skema konsolidasi SEBATIK.

Membuat skema target docs/refactoring/model-data.md §3 dari nol: satu dimensi
`indikator`, satu `metadata_indikator`, dan satu tabel fakta `nilai_indikator`
yang menggantikan enam tabel nilai lama.

Migrasi ini tidak menyentuh basis data SQLite lama; pemindahan datanya
dikerjakan scripts/migrasi_sqlite_ke_target.py (Fase 2).

Revision ID: 0001_baseline
Revises:
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "indikator",
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("kategori", sa.String(length=8), nullable=False),
        sa.Column("nomor", sa.Integer(), nullable=True),
        sa.Column("kode_indikator", sa.String(length=32), nullable=True),
        sa.Column("nama_indikator", sa.Text(), nullable=False),
        sa.Column("nama_asli", sa.Text(), nullable=True),
        sa.Column("kelompok", sa.Text(), nullable=True),
        sa.Column("arah_pembangunan", sa.Text(), nullable=True),
        sa.Column("sasaran_visi", sa.Text(), nullable=True),
        sa.Column("misi_agenda", sa.Text(), nullable=True),
        sa.Column("arah_ie", sa.Text(), nullable=True),
        sa.Column("indikator_induk", sa.Text(), nullable=True),
        sa.Column("kelompok_makro", sa.Text(), nullable=True),
        sa.Column("satuan", sa.String(length=120), nullable=True),
        sa.Column("penghasil", sa.Text(), nullable=True),
        sa.Column("kl_pengampu", sa.Text(), nullable=True),
        sa.Column("opd_pengampu", sa.Text(), nullable=True),
        sa.Column("tim_pjk", sa.String(length=120), nullable=True),
        sa.Column("sumber_data", sa.Text(), nullable=True),
        sa.Column("frekuensi", sa.Text(), nullable=True),
        sa.Column("status_ketersediaan", sa.String(length=60), nullable=True),
        sa.Column("status_metadata", sa.String(length=60), nullable=True),
        sa.Column("periode_data", sa.String(length=60), nullable=True),
        sa.Column("tahun_terakhir", sa.Integer(), nullable=True),
        sa.Column("is_proxy", sa.Boolean(), nullable=False),
        sa.Column("nama_proxy", sa.Text(), nullable=True),
        sa.Column("status_rpjmd", sa.String(length=40), nullable=True),
        sa.Column("arah_baik", sa.String(length=10), nullable=True),
        sa.Column("arah_baik_terverifikasi", sa.Boolean(), nullable=False),
        sa.Column("kode_sdgs", sa.String(length=40), nullable=True),
        sa.Column("link_metadata", sa.Text(), nullable=True),
        sa.Column("link_publikasi", sa.Text(), nullable=True),
        sa.Column("link_data", sa.Text(), nullable=True),
        sa.Column("catatan_teknis", sa.Text(), nullable=True),
        sa.Column("sumber_master", sa.Text(), nullable=True),
        sa.Column("status_verifikasi", sa.String(length=24), nullable=False),
        sa.Column(
            "diverifikasi_pada",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.CheckConstraint("arah_baik IS NULL OR arah_baik IN ('NAIK','TURUN')", name="ck_indikator_arah_baik"),
        sa.PrimaryKeyConstraint("id_indikator"),
    )
    with op.batch_alter_table("indikator", schema=None) as batch_op:
        batch_op.create_index("ix_indikator_kategori", ["kategori"], unique=False)
        batch_op.create_index("ix_indikator_kelompok_makro", ["kelompok_makro"], unique=False)
        batch_op.create_index("ix_indikator_status_verifikasi", ["status_verifikasi"], unique=False)

    op.create_table(
        "wilayah",
        sa.Column("kode", sa.String(length=10), nullable=False),
        sa.Column("nama", sa.String(length=120), nullable=False),
        sa.Column("tingkat", sa.String(length=20), nullable=False),
        sa.Column("parent_kode", sa.String(length=10), nullable=True),
        sa.Column("aktif", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_kode"],
            ["wilayah.kode"],
        ),
        sa.PrimaryKeyConstraint("kode"),
    )
    op.create_table(
        "metadata_indikator",
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("definisi", sa.Text(), nullable=True),
        sa.Column("interpretasi", sa.Text(), nullable=True),
        sa.Column("sumber_data", sa.Text(), nullable=True),
        sa.Column("frekuensi", sa.Text(), nullable=True),
        sa.Column("rumus", sa.Text(), nullable=True),
        sa.Column("rumus_mentah", sa.Text(), nullable=True),
        sa.Column("rumus_latex", sa.Text(), nullable=True),
        sa.Column("halaman_sumber", sa.String(length=40), nullable=True),
        sa.Column("perlu_verifikasi_manual", sa.Boolean(), nullable=False),
        sa.Column("sumber_metadata", sa.String(length=120), nullable=True),
        sa.Column("nama_di_buku1", sa.Text(), nullable=True),
        sa.Column("status_metadata", sa.String(length=60), nullable=True),
        sa.ForeignKeyConstraint(["id_indikator"], ["indikator.id_indikator"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_indikator"),
    )
    op.create_table(
        "pengguna",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("nama", sa.String(length=160), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("peran", sa.String(length=20), nullable=False),
        sa.Column("tim_pjk", sa.String(length=120), nullable=True),
        sa.Column("wilayah_kode", sa.String(length=10), nullable=True),
        sa.Column("aktif", sa.Boolean(), nullable=False),
        sa.Column("harus_ganti_password", sa.Boolean(), nullable=False),
        sa.Column(
            "dibuat_pada", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.CheckConstraint("peran IN ('ADMIN','OPERATOR','VERIFIKATOR','PENGUNJUNG')", name="ck_pengguna_peran"),
        sa.ForeignKeyConstraint(
            ["wilayah_kode"],
            ["wilayah.kode"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "penugasan_pic",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("jenis_pic", sa.String(length=40), nullable=False),
        sa.Column("nama_pic", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["id_indikator"], ["indikator.id_indikator"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("penugasan_pic", schema=None) as batch_op:
        batch_op.create_index("ix_penugasan_pic_indikator", ["id_indikator"], unique=False)

    op.create_table(
        "snapshot_ketersediaan",
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("tanggal_snapshot", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.ForeignKeyConstraint(["id_indikator"], ["indikator.id_indikator"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_indikator", "tanggal_snapshot"),
    )
    op.create_table(
        "log_aktivitas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("waktu", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("pengguna_id", sa.Integer(), nullable=True),
        sa.Column("aksi", sa.String(length=60), nullable=False),
        sa.Column("objek_tipe", sa.String(length=60), nullable=True),
        sa.Column("objek_id", sa.String(length=60), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pengguna_id"],
            ["pengguna.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("log_aktivitas", schema=None) as batch_op:
        batch_op.create_index("ix_log_aktivitas_waktu", ["waktu"], unique=False)

    op.create_table(
        "log_perubahan",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("waktu", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("pengguna_id", sa.Integer(), nullable=True),
        sa.Column("id_indikator", sa.String(length=16), nullable=True),
        sa.Column("field", sa.String(length=80), nullable=False),
        sa.Column("nilai_lama", sa.Text(), nullable=True),
        sa.Column("nilai_baru", sa.Text(), nullable=True),
        sa.Column("sumber_perubahan", sa.String(length=40), nullable=False),
        sa.Column("referensi_id", sa.String(length=40), nullable=True),
        sa.Column("catatan", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["id_indikator"],
            ["indikator.id_indikator"],
        ),
        sa.ForeignKeyConstraint(
            ["pengguna_id"],
            ["pengguna.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("log_perubahan", schema=None) as batch_op:
        batch_op.create_index("ix_log_perubahan_waktu", ["waktu"], unique=False)

    op.create_table(
        "unggahan_excel",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nama_file_asli", sa.Text(), nullable=False),
        sa.Column("path_arsip", sa.Text(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ringkasan_diff", sa.Text(), nullable=True),
        sa.Column("pengguna_id", sa.Integer(), nullable=True),
        sa.Column(
            "dibuat_pada", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.Column("disetujui_pada", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["pengguna_id"],
            ["pengguna.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "usulan_nilai",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("wilayah_kode", sa.String(length=10), nullable=True),
        sa.Column("tahun", sa.Integer(), nullable=False),
        sa.Column("jenis", sa.String(length=12), nullable=False),
        sa.Column("periode", sa.Integer(), nullable=True),
        sa.Column("nilai", sa.Numeric(precision=20, scale=6), nullable=False),
        sa.Column("sumber", sa.Text(), nullable=False),
        sa.Column("catatan", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("pengusul_id", sa.Integer(), nullable=False),
        sa.Column("verifikator_id", sa.Integer(), nullable=True),
        sa.Column("alasan_verifikasi", sa.Text(), nullable=True),
        sa.Column(
            "dibuat_pada", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.Column("dikirim_pada", sa.DateTime(timezone=True), nullable=True),
        sa.Column("diverifikasi_pada", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("jenis IN ('realisasi','target')", name="ck_usulan_jenis"),
        sa.CheckConstraint("status IN ('MENUNGGU_VERIFIKASI','DISETUJUI','DITOLAK')", name="ck_usulan_status"),
        sa.CheckConstraint("periode IS NULL OR periode BETWEEN 1 AND 4", name="ck_usulan_periode"),
        sa.ForeignKeyConstraint(
            ["id_indikator"],
            ["indikator.id_indikator"],
        ),
        sa.ForeignKeyConstraint(
            ["pengusul_id"],
            ["pengguna.id"],
        ),
        sa.ForeignKeyConstraint(
            ["verifikator_id"],
            ["pengguna.id"],
        ),
        sa.ForeignKeyConstraint(
            ["wilayah_kode"],
            ["wilayah.kode"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("usulan_nilai", schema=None) as batch_op:
        batch_op.create_index("ix_usulan_pengusul", ["pengusul_id"], unique=False)
        batch_op.create_index("ix_usulan_status", ["status"], unique=False)
        batch_op.create_index("ix_usulan_wilayah", ["wilayah_kode"], unique=False)

    op.create_table(
        "bukti_dukung",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usulan_id", sa.Integer(), nullable=False),
        sa.Column("nama_file", sa.Text(), nullable=False),
        sa.Column("path_file", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column("ukuran", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "diunggah_pada", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False
        ),
        sa.ForeignKeyConstraint(["usulan_id"], ["usulan_nilai.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("bukti_dukung", schema=None) as batch_op:
        batch_op.create_index("ix_bukti_usulan", ["usulan_id"], unique=False)

    op.create_table(
        "nilai_indikator",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_indikator", sa.String(length=16), nullable=False),
        sa.Column("wilayah_kode", sa.String(length=10), nullable=False),
        sa.Column("tahun", sa.Integer(), nullable=False),
        sa.Column("jenis", sa.String(length=12), nullable=False),
        sa.Column("periode", sa.Integer(), nullable=True),
        sa.Column("nilai", sa.Numeric(precision=20, scale=6, asdecimal=False), nullable=True),
        sa.Column("nilai_teks", sa.Text(), nullable=True),
        sa.Column("label_periode", sa.String(length=40), nullable=True),
        sa.Column("satuan_catatan", sa.Text(), nullable=True),
        sa.Column("sumber", sa.Text(), nullable=True),
        sa.Column("usulan_id", sa.Integer(), nullable=True),
        sa.Column("status_verifikasi", sa.String(length=24), nullable=False),
        sa.Column("diverifikasi_pada", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("jenis IN ('realisasi','target')", name="ck_nilai_indikator_jenis"),
        sa.CheckConstraint(
            "status_verifikasi IN ('MENUNGGU_VERIFIKASI','DISETUJUI','DITOLAK')", name="ck_nilai_indikator_status"
        ),
        sa.CheckConstraint("periode IS NULL OR periode BETWEEN 1 AND 4", name="ck_nilai_indikator_periode"),
        sa.ForeignKeyConstraint(["id_indikator"], ["indikator.id_indikator"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usulan_id"], ["usulan_nilai.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["wilayah_kode"],
            ["wilayah.kode"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("nilai_indikator", schema=None) as batch_op:
        batch_op.create_index(
            "ix_nilai_indikator_seri", ["id_indikator", "wilayah_kode", "jenis", "tahun"], unique=False
        )
        batch_op.create_index("ix_nilai_indikator_tahun", ["tahun", "jenis", "status_verifikasi"], unique=False)
        batch_op.create_index("ix_nilai_indikator_usulan", ["usulan_id"], unique=False)
        batch_op.create_index(
            "uq_nilai_indikator_periodik",
            ["id_indikator", "wilayah_kode", "tahun", "jenis", "periode"],
            unique=True,
            sqlite_where=sa.text("periode IS NOT NULL"),
            postgresql_where=sa.text("periode IS NOT NULL"),
        )
        batch_op.create_index(
            "uq_nilai_indikator_tahunan",
            ["id_indikator", "wilayah_kode", "tahun", "jenis"],
            unique=True,
            sqlite_where=sa.text("periode IS NULL"),
            postgresql_where=sa.text("periode IS NULL"),
        )


def downgrade() -> None:
    with op.batch_alter_table("nilai_indikator", schema=None) as batch_op:
        batch_op.drop_index(
            "uq_nilai_indikator_tahunan",
            sqlite_where=sa.text("periode IS NULL"),
            postgresql_where=sa.text("periode IS NULL"),
        )
        batch_op.drop_index(
            "uq_nilai_indikator_periodik",
            sqlite_where=sa.text("periode IS NOT NULL"),
            postgresql_where=sa.text("periode IS NOT NULL"),
        )
        batch_op.drop_index("ix_nilai_indikator_usulan")
        batch_op.drop_index("ix_nilai_indikator_tahun")
        batch_op.drop_index("ix_nilai_indikator_seri")

    op.drop_table("nilai_indikator")
    with op.batch_alter_table("bukti_dukung", schema=None) as batch_op:
        batch_op.drop_index("ix_bukti_usulan")

    op.drop_table("bukti_dukung")
    with op.batch_alter_table("usulan_nilai", schema=None) as batch_op:
        batch_op.drop_index("ix_usulan_wilayah")
        batch_op.drop_index("ix_usulan_status")
        batch_op.drop_index("ix_usulan_pengusul")

    op.drop_table("usulan_nilai")
    op.drop_table("unggahan_excel")
    with op.batch_alter_table("log_perubahan", schema=None) as batch_op:
        batch_op.drop_index("ix_log_perubahan_waktu")

    op.drop_table("log_perubahan")
    with op.batch_alter_table("log_aktivitas", schema=None) as batch_op:
        batch_op.drop_index("ix_log_aktivitas_waktu")

    op.drop_table("log_aktivitas")
    op.drop_table("snapshot_ketersediaan")
    with op.batch_alter_table("penugasan_pic", schema=None) as batch_op:
        batch_op.drop_index("ix_penugasan_pic_indikator")

    op.drop_table("penugasan_pic")
    op.drop_table("pengguna")
    op.drop_table("metadata_indikator")
    op.drop_table("wilayah")
    with op.batch_alter_table("indikator", schema=None) as batch_op:
        batch_op.drop_index("ix_indikator_status_verifikasi")
        batch_op.drop_index("ix_indikator_kelompok_makro")
        batch_op.drop_index("ix_indikator_kategori")

    op.drop_table("indikator")

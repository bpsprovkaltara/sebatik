"""Query terhadap tabel fakta tunggal `nilai_indikator`.

Menggantikan seluruh SQL mentah yang dulu tersebar untuk enam tabel nilai.
Aturan yang dipakai berulang:

- Hanya baris `DISETUJUI` yang boleh terbaca endpoint publik.
- `periode IS NULL` = nilai tahunan; `periode` terisi = rilis semester.
- Nilai periode terbaru menggantikan nilai tahunan saat ditampilkan.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, Indikator, JenisNilai, NilaiIndikator, StatusVerifikasi


def _disetujui(stmt: Select) -> Select:
    return stmt.where(NilaiIndikator.status_verifikasi == StatusVerifikasi.DISETUJUI)


def _lingkup(
    stmt: Select,
    id_indikator: str,
    wilayah_kode: str,
    jenis: str | None = None,
    *,
    tahunan: bool = True,
) -> Select:
    stmt = stmt.where(
        NilaiIndikator.id_indikator == id_indikator,
        NilaiIndikator.wilayah_kode == wilayah_kode,
    )
    if jenis is not None:
        stmt = stmt.where(NilaiIndikator.jenis == jenis)
    if tahunan:
        stmt = stmt.where(NilaiIndikator.periode.is_(None))
    return _disetujui(stmt)


def tahun_realisasi_tersedia(session: Session) -> list[int]:
    """Tahun-tahun yang punya realisasi disetujui, menaik."""
    stmt = _disetujui(
        select(NilaiIndikator.tahun).where(NilaiIndikator.jenis == JenisNilai.REALISASI).distinct()
    ).order_by(NilaiIndikator.tahun)
    return list(session.scalars(stmt))


def ambil(
    session: Session,
    id_indikator: str,
    wilayah_kode: str,
    tahun: int,
    jenis: str,
) -> NilaiIndikator | None:
    """Satu nilai tahunan untuk (indikator, wilayah, tahun, jenis)."""
    stmt = _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, jenis).where(NilaiIndikator.tahun == tahun)
    return session.scalars(stmt).first()


def nilai_periode_terbaru(
    session: Session,
    id_indikator: str,
    wilayah_kode: str,
    tahun: int,
    jenis: str = JenisNilai.REALISASI,
) -> NilaiIndikator | None:
    """Rilis periode paling akhir yang sudah disetujui pada satu tahun.

    Menggantikan `latest_period_value` lama yang bercabang antara tabel provinsi
    dan tabel wilayah.
    """
    stmt = (
        _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, jenis, tahunan=False)
        .where(NilaiIndikator.tahun == tahun, NilaiIndikator.periode.is_not(None))
        .order_by(NilaiIndikator.periode.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def sebelum_tahun(
    session: Session,
    id_indikator: str,
    wilayah_kode: str,
    tahun: int,
    jenis: str = JenisNilai.REALISASI,
) -> NilaiIndikator | None:
    """Nilai tahunan terdekat sebelum `tahun` (untuk menghitung perubahan)."""
    stmt = (
        _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, jenis)
        .where(NilaiIndikator.tahun < tahun)
        .order_by(NilaiIndikator.tahun.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def terakhir_terisi(
    session: Session,
    id_indikator: str,
    wilayah_kode: str,
    sampai_tahun: int,
    jenis: str = JenisNilai.REALISASI,
) -> NilaiIndikator | None:
    """Nilai tahunan terisi paling akhir hingga `sampai_tahun` inklusif."""
    stmt = (
        _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, jenis)
        .where(
            NilaiIndikator.tahun <= sampai_tahun,
            (NilaiIndikator.nilai.is_not(None)) | (NilaiIndikator.nilai_teks.is_not(None)),
        )
        .order_by(NilaiIndikator.tahun.desc())
        .limit(1)
    )
    return session.scalars(stmt).first()


def seri(
    session: Session,
    id_indikator: str,
    wilayah_kode: str,
    jenis: str | None = None,
) -> list[NilaiIndikator]:
    """Seri tampilan: rilis terbaru menang dan celah 2021–2025 diisi nilai terdekat.

    Baris sintetis hanya hidup di memori dan tidak pernah ditulis ke tabel
    fakta. Saat nilai asli untuk tahun tersebut disetujui, hasil query berikutnya
    otomatis memakai nilai asli itu.
    """
    stmt = _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, jenis, tahunan=False).order_by(
        NilaiIndikator.tahun, NilaiIndikator.jenis, NilaiIndikator.periode.asc().nullsfirst()
    )
    semua = list(session.scalars(stmt))
    # Karena periodenya diurutkan menaik, penetapan terakhir pada kunci yang
    # sama adalah rilis semester/triwulan paling mutakhir.
    terpilih = {(baris.tahun, baris.jenis): baris for baris in semua}
    realisasi = {
        tahun: baris
        for (tahun, jenis_baris), baris in terpilih.items()
        if jenis_baris == JenisNilai.REALISASI
        and 2021 <= tahun <= 2025
        and (baris.nilai is not None or baris.nilai_teks is not None)
    }
    if realisasi:
        for tahun in range(2021, 2026):
            if (tahun, JenisNilai.REALISASI) in terpilih:
                continue
            sumber = min(realisasi.values(), key=lambda baris: (abs(baris.tahun - tahun), baris.tahun))
            terpilih[(tahun, JenisNilai.REALISASI)] = NilaiIndikator(
                id_indikator=sumber.id_indikator,
                wilayah_kode=sumber.wilayah_kode,
                tahun=tahun,
                jenis=JenisNilai.REALISASI,
                periode=sumber.periode,
                nilai=sumber.nilai,
                nilai_teks=sumber.nilai_teks,
                label_periode=sumber.label_periode,
                satuan_catatan=f"Menggunakan nilai terdekat tahun {sumber.tahun}",
                sumber=sumber.sumber,
                status_verifikasi=StatusVerifikasi.DISETUJUI,
            )
    return [terpilih[kunci] for kunci in sorted(terpilih)]


def seri_lengkap(session: Session, id_indikator: str, wilayah_kode: str) -> list[NilaiIndikator]:
    """Seri tahunan dan periodik sekaligus (dipakai endpoint metadata)."""
    stmt = _disetujui(
        select(NilaiIndikator).where(
            NilaiIndikator.id_indikator == id_indikator,
            NilaiIndikator.wilayah_kode == wilayah_kode,
        )
    ).order_by(NilaiIndikator.tahun, NilaiIndikator.jenis, NilaiIndikator.periode)
    return list(session.scalars(stmt))


def hitung_slot_terisi(
    session: Session,
    id_indikator: Sequence[str],
    tahun_awal: int,
    tahun_akhir: int,
) -> int:
    """Jumlah slot realisasi tahunan terisi pada rentang tahun tertentu."""
    if not id_indikator:
        return 0
    stmt = _disetujui(
        select(func.count())
        .select_from(NilaiIndikator)
        .where(
            NilaiIndikator.id_indikator.in_(id_indikator),
            NilaiIndikator.jenis == JenisNilai.REALISASI,
            NilaiIndikator.periode.is_(None),
            NilaiIndikator.tahun.between(tahun_awal, tahun_akhir),
            (NilaiIndikator.nilai.is_not(None)) | (NilaiIndikator.nilai_teks.is_not(None)),
        )
    )
    return session.scalar(stmt) or 0


def hitung_terisi_tahun(
    session: Session,
    id_indikator: Sequence[str],
    wilayah_kode: str,
    tahun: int,
) -> int:
    """Jumlah indikator yang memiliki realisasi tahunan atau periodik pada satu wilayah."""
    if not id_indikator:
        return 0
    stmt = _disetujui(
        select(func.count(func.distinct(NilaiIndikator.id_indikator)))
        .select_from(NilaiIndikator)
        .where(
            NilaiIndikator.id_indikator.in_(id_indikator),
            NilaiIndikator.wilayah_kode == wilayah_kode,
            NilaiIndikator.jenis == JenisNilai.REALISASI,
            NilaiIndikator.tahun == tahun,
            (NilaiIndikator.nilai.is_not(None)) | (NilaiIndikator.nilai_teks.is_not(None)),
        )
    )
    return session.scalar(stmt) or 0


def diverifikasi_terakhir(session: Session, id_indikator: str, wilayah_kode: str) -> NilaiIndikator | None:
    """Baris realisasi terisi dengan waktu verifikasi paling akhir."""
    stmt = (
        _lingkup(select(NilaiIndikator), id_indikator, wilayah_kode, JenisNilai.REALISASI)
        .where((NilaiIndikator.nilai.is_not(None)) | (NilaiIndikator.nilai_teks.is_not(None)))
        .order_by(NilaiIndikator.diverifikasi_pada.desc().nullslast())
        .limit(1)
    )
    return session.scalars(stmt).first()


def upsert(
    session: Session,
    *,
    id_indikator: str,
    wilayah_kode: str,
    tahun: int,
    jenis: str,
    periode: int | None = None,
    nilai: float | None = None,
    nilai_teks: str | None = None,
    label_periode: str | None = None,
    satuan_catatan: str | None = None,
    sumber: str | None = None,
    usulan_id: int | None = None,
    status_verifikasi: str = StatusVerifikasi.DISETUJUI,
    diverifikasi_pada: datetime | None = None,
) -> tuple[NilaiIndikator, float | None]:
    """Sisipkan atau perbarui satu baris fakta.

    Mengembalikan barisnya beserta nilai lamanya (None bila baru), sehingga
    pemanggil dapat mencatat log perubahan tanpa query tambahan.

    Tidak memakai `ON CONFLICT` dialek tertentu supaya jalur tulis yang sama
    berlaku di SQLite maupun PostgreSQL.
    """
    stmt = select(NilaiIndikator).where(
        NilaiIndikator.id_indikator == id_indikator,
        NilaiIndikator.wilayah_kode == wilayah_kode,
        NilaiIndikator.tahun == tahun,
        NilaiIndikator.jenis == jenis,
        NilaiIndikator.periode.is_(None) if periode is None else NilaiIndikator.periode == periode,
    )
    baris = session.scalars(stmt).first()
    nilai_lama = baris.nilai if baris else None

    if baris is None:
        baris = NilaiIndikator(
            id_indikator=id_indikator,
            wilayah_kode=wilayah_kode,
            tahun=tahun,
            jenis=jenis,
            periode=periode,
        )
        session.add(baris)

    baris.nilai = nilai
    baris.nilai_teks = nilai_teks
    baris.label_periode = label_periode
    baris.satuan_catatan = satuan_catatan
    baris.sumber = sumber
    baris.usulan_id = usulan_id
    baris.status_verifikasi = status_verifikasi
    baris.diverifikasi_pada = diverifikasi_pada or datetime.now(UTC)
    return baris, nilai_lama


def semua_nilai_provinsi(session: Session) -> list[NilaiIndikator]:
    """Seluruh nilai tahunan provinsi — dipakai penyusunan diff unggahan massal."""
    stmt = select(NilaiIndikator).where(
        NilaiIndikator.wilayah_kode == KODE_PROVINSI,
        NilaiIndikator.periode.is_(None),
    )
    return list(session.scalars(stmt))


def semua_indikator_ringkas(session: Session) -> list[Indikator]:
    """Dimensi indikator seadanya, tanpa filter verifikasi (untuk diff)."""
    return list(session.scalars(select(Indikator)))

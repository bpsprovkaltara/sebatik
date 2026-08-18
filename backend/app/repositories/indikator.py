"""Query terhadap dimensi indikator dan metadatanya."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session

from ..models import Indikator, MetadataIndikator, StatusVerifikasi

# Kolom yang boleh keluar lewat endpoint publik `/indikator`. Nama PIC
# perorangan dan status ketersediaan sengaja tidak termasuk.
FIELD_PUBLIK = (
    "id_indikator",
    "nama_indikator",
    "kategori",
    "kelompok",
    "satuan",
    "tim_pjk",
    "opd_pengampu",
    "status_metadata",
    "tahun_terakhir",
    "is_proxy",
)


def _terverifikasi(stmt: Select) -> Select:
    """Filter yang berulang di hampir semua pembacaan publik."""
    return stmt.where(Indikator.status_verifikasi == StatusVerifikasi.DISETUJUI)


def ambil(session: Session, id_indikator: str) -> Indikator | None:
    return session.get(Indikator, id_indikator)


def ambil_terverifikasi(session: Session, id_indikator: str) -> Indikator | None:
    stmt = _terverifikasi(select(Indikator).where(Indikator.id_indikator == id_indikator))
    return session.scalars(stmt).first()


def ada(session: Session, id_indikator: str) -> bool:
    stmt = select(Indikator.id_indikator).where(Indikator.id_indikator == id_indikator)
    return session.scalars(stmt).first() is not None


def _saring(
    stmt: Select,
    q: str | None = None,
    kategori: Sequence[str] | None = None,
    kelompok: Sequence[str] | None = None,
    tim: Sequence[str] | None = None,
    status_metadata: Sequence[str] | None = None,
) -> Select:
    if q:
        stmt = stmt.where(Indikator.nama_indikator.ilike(f"%{q}%"))
    if kategori:
        stmt = stmt.where(Indikator.kategori.in_(kategori))
    if kelompok:
        stmt = stmt.where(Indikator.kelompok.in_(kelompok))
    if tim:
        stmt = stmt.where(Indikator.tim_pjk.in_(tim))
    if status_metadata:
        stmt = stmt.where(Indikator.status_metadata.in_(status_metadata))
    return stmt


def cari(
    session: Session,
    *,
    q: str | None = None,
    kategori: Sequence[str] | None = None,
    kelompok: Sequence[str] | None = None,
    tim: Sequence[str] | None = None,
    status_metadata: Sequence[str] | None = None,
    sort: str = "id_indikator",
    order: str = "asc",
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[Indikator], int]:
    """Halaman hasil beserta totalnya (untuk endpoint `/indikator`)."""

    def disaring(stmt: Select) -> Select:
        return _saring(stmt, q, kategori, kelompok, tim, status_metadata)

    # `is_proxy` boolean tidak berguna sebagai kunci urut dan tidak pernah
    # dikirim frontend; jatuhkan ke id_indikator bila diminta.
    kolom_urut = {nama: getattr(Indikator, nama) for nama in FIELD_PUBLIK if nama != "is_proxy"}
    kolom = kolom_urut.get(sort, Indikator.id_indikator)
    arah = desc if order == "desc" else asc

    daftar = session.scalars(
        disaring(select(Indikator)).order_by(arah(kolom)).offset((page - 1) * page_size).limit(page_size)
    ).all()
    total = session.scalar(disaring(select(func.count()).select_from(Indikator))) or 0
    return list(daftar), total


def daftar_ekspor(session: Session) -> list[Indikator]:
    """Urutan ekspor: IUP lalu ISV (kategori menurun), lalu nomor urut."""
    stmt = select(Indikator).order_by(Indikator.kategori.desc(), Indikator.nomor)
    return list(session.scalars(stmt))


def daftar_terverifikasi(session: Session) -> list[Indikator]:
    stmt = _terverifikasi(select(Indikator)).order_by(Indikator.id_indikator)
    return list(session.scalars(stmt))


def daftar_makro(session: Session) -> list[Indikator]:
    """Indikator berklasifikasi makro, ISV lebih dulu (kategori menurun)."""
    stmt = _terverifikasi(select(Indikator).where(Indikator.kelompok_makro.like("Makro%"))).order_by(
        Indikator.kategori.desc(), Indikator.id_indikator
    )
    return list(session.scalars(stmt))


def daftar_sasaran_visi(session: Session) -> list[Indikator]:
    stmt = _terverifikasi(select(Indikator).where(Indikator.kategori == "ISV")).order_by(Indikator.id_indikator)
    return list(session.scalars(stmt))


def id_berklasifikasi(session: Session, kolom: str) -> list[str]:
    """ID indikator yang punya isi bermakna pada kolom klasifikasi tertentu.

    Nilai kosong dan penanda strip (`-`, `- belum ditetapkan`) dianggap belum
    diklasifikasikan, sama seperti perhitungan ketersediaan sebelumnya.
    """
    atribut = getattr(Indikator, kolom)
    stmt = _terverifikasi(
        select(Indikator.id_indikator).where(
            atribut.is_not(None),
            func.trim(atribut) != "",
            atribut.not_like("-%"),
        )
    )
    return list(session.scalars(stmt))


def daftar_arah_terverifikasi(session: Session) -> list[Indikator]:
    """Indikator yang arah baiknya sudah dikonfirmasi admin.

    Hanya indikator ini yang boleh masuk peringkat: tanpa arah yang pasti,
    "membaik" dan "memburuk" tidak dapat dibedakan.
    """
    stmt = select(Indikator).where(Indikator.arah_baik_terverifikasi.is_(True))
    return list(session.scalars(stmt))


def ambil_metadata(session: Session, id_indikator: str) -> MetadataIndikator | None:
    return session.get(MetadataIndikator, id_indikator)


def ubah_arah_baik(indikator: Indikator, arah_baik: str) -> str | None:
    """Set arah baik sebagai terverifikasi; mengembalikan nilai lama untuk log audit.

    Menerima objek, bukan id, supaya "indikator tidak ditemukan" ditangani
    pemanggil dan tidak tertukar dengan "arah lama memang NULL".
    """
    lama = indikator.arah_baik
    indikator.arah_baik = arah_baik
    indikator.arah_baik_terverifikasi = True
    return lama

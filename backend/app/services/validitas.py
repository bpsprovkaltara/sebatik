"""Penyusunan muatan validitas: status verifikasi dan jejak pembaruan.

Perhitungan status indikator dan penentuan siapa pembaru terakhir dipisahkan
dari router karena keduanya aturan bisnis, bukan HTTP (backend.md §1.2).
"""

from __future__ import annotations

from typing import Any, NamedTuple

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, Indikator, Peran, Wilayah
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories import wilayah as repo_wilayah
from .beranda import STATUS_HANYA_TERVERIFIKASI
from .indikator import FIELD_METADATA_BERMAKNA

# Batas aman: sebelumnya endpoint ini mengembalikan seluruh baris tanpa batas.
BATAS_MAKSIMUM = 200

STATUS_PROXY = "Proxy"
STATUS_TERSEDIA = "Tersedia"
STATUS_BELUM_TERSEDIA = "Belum Tersedia"
PENGAMPU_BELUM_DITETAPKAN = "Belum ditetapkan"
# Nilai master provinsi tanpa jejak usulan berasal dari basis data yang dimuat
# admin, bukan dari alur operator.
PEMBARU_MASTER = "Admin Provinsi"


class Pembaru(NamedTuple):
    nama: str | None
    peran: str | None


def pembaru_terakhir(
    *, nama_pengusul: str | None, peran_pengusul: str | None, tersedia: bool, wilayah_kode: str
) -> Pembaru:
    """Siapa yang terakhir memperbarui nilai indikator ini."""
    if nama_pengusul is not None:
        return Pembaru(nama_pengusul, peran_pengusul)
    if tersedia and wilayah_kode == KODE_PROVINSI:
        return Pembaru(PEMBARU_MASTER, Peran.ADMIN.value)
    return Pembaru(None, None)


def status_indikator(*, is_proxy: bool, tersedia: bool) -> str:
    if is_proxy and tersedia:
        return STATUS_PROXY
    return STATUS_TERSEDIA if tersedia else STATUS_BELUM_TERSEDIA


def saring(daftar: list[Indikator], q: str | None) -> list[Indikator]:
    if not q:
        return daftar
    kunci = q.lower()
    return [
        item
        for item in daftar
        if kunci in (item.nama_indikator or "").lower() or kunci in (item.kode_indikator or "").lower()
    ]


def _baris(
    session: Session,
    item: Indikator,
    *,
    wilayah_kode: str,
    peran: str | None,
    pengguna_id: int | None,
    boleh_lihat_bukti: bool,
) -> dict[str, Any]:
    terakhir = repo_nilai.diverifikasi_terakhir(session, item.id_indikator, wilayah_kode)
    usulan = repo_tata_kelola.ambil_usulan(session, terakhir.usulan_id) if terakhir and terakhir.usulan_id else None
    pengusul = repo_tata_kelola.ambil_pengusul(session, usulan.pengusul_id) if usulan else None

    tersedia = terakhir is not None
    diverifikasi_pada = terakhir.diverifikasi_pada if terakhir else None
    pembaru = pembaru_terakhir(
        nama_pengusul=pengusul.nama if pengusul else None,
        peran_pengusul=pengusul.peran if pengusul else None,
        tersedia=tersedia,
        wilayah_kode=wilayah_kode,
    )

    metadata = repo_indikator.ambil_metadata(session, item.id_indikator)
    metadata_tersedia = bool(metadata and any(getattr(metadata, f) for f in FIELD_METADATA_BERMAKNA))
    bukti = repo_tata_kelola.daftar_bukti(session, usulan.id) if usulan else []
    # Operator hanya boleh melihat bukti pada usulannya sendiri.
    boleh = boleh_lihat_bukti or (peran == Peran.OPERATOR and usulan is not None and usulan.pengusul_id == pengguna_id)
    return {
        "id_indikator": item.id_indikator,
        "kode_indikator": item.kode_indikator,
        "nama_indikator": item.nama_indikator,
        "satuan": item.satuan,
        "instansi_pengampu": item.opd_pengampu or PENGAMPU_BELUM_DITETAPKAN,
        "validasi": f"Terverifikasi tanggal {diverifikasi_pada}" if diverifikasi_pada else "Belum diverifikasi",
        "terverifikasi_pada": diverifikasi_pada,
        "update": f"Terakhir update tanggal {diverifikasi_pada} oleh {pembaru.nama}"
        if diverifikasi_pada and pembaru.nama
        else "Belum ada pembaruan",
        "update_oleh": pembaru.nama,
        "peran_update": pembaru.peran,
        "status_indikator": status_indikator(is_proxy=bool(item.is_proxy), tersedia=tersedia),
        "metadata_tersedia": metadata_tersedia,
        "usulan_id": usulan.id if usulan else None,
        "bukti_dukung_jumlah": len(bukti),
        "bukti_dukung": [
            {
                "id": b.id,
                "nama_file": b.nama_file,
                "mime_type": b.mime_type,
                "ukuran": b.ukuran,
                "diunggah_pada": b.diunggah_pada,
            }
            for b in bukti
        ]
        if boleh
        else [],
    }


def susun(
    session: Session,
    wilayah: Wilayah,
    *,
    q: str | None,
    page: int,
    page_size: int,
    peran: str | None,
    pengguna_id: int | None,
) -> dict[str, Any]:
    """Muatan lengkap `/validitas` untuk satu wilayah, berhalaman."""
    indikator = saring(repo_indikator.daftar_terverifikasi(session), q)
    total = len(indikator)
    halaman = indikator[(page - 1) * page_size : page * page_size]
    boleh_lihat_bukti = peran in {Peran.ADMIN, Peran.VERIFIKATOR}

    return {
        "wilayah": {"kode": wilayah.kode, "nama": wilayah.nama, "tingkat": wilayah.tingkat},
        "wilayah_opsi": [
            {"kode": w.kode, "nama": w.nama, "tingkat": w.tingkat} for w in repo_wilayah.daftar_aktif(session)
        ],
        "data": [
            _baris(
                session,
                item,
                wilayah_kode=wilayah.kode,
                peran=peran,
                pengguna_id=pengguna_id,
                boleh_lihat_bukti=boleh_lihat_bukti,
            )
            for item in halaman
        ],
        "total": total,
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }

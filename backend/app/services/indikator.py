"""Penyusunan muatan indikator: daftar publik, detail, dan metadata.

Termasuk aturan kecil yang tidak boleh tinggal di router: kolom mana yang
boleh keluar ke publik, nama kolom lama yang masih dipertahankan demi kontrak,
dan kapan sebuah metadata layak disebut "tersedia" (backend.md §1.2).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, ArahBaik, Indikator
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola
from . import capaian as svc_capaian

# Kolom yang boleh keluar lewat daftar publik. Nama PIC perorangan dan status
# ketersediaan sengaja tidak termasuk.
FIELD_PUBLIK = repo_indikator.FIELD_PUBLIK

# Kompatibilitas kontrak: kolom basis data dibakukan menjadi `opd_pengampu`,
# tetapi frontend lama masih membaca `opd_penanggung_jawab`.
NAMA_LAMA = {"opd_pengampu": "opd_penanggung_jawab"}

# Isi metadata yang menentukan apakah metadata dianggap benar-benar tersedia.
FIELD_METADATA_BERMAKNA = ("definisi", "rumus_mentah", "interpretasi", "sumber_data", "frekuensi")


def ringkas(indikator: Indikator) -> dict[str, Any]:
    """Satu baris daftar publik, dengan nama kolom lama dipertahankan."""
    return {NAMA_LAMA.get(f, f): getattr(indikator, f) for f in FIELD_PUBLIK}


def cari(
    session: Session,
    *,
    q: str | None,
    kategori: list[str] | None,
    kelompok: list[str] | None,
    tim: list[str] | None,
    status_metadata: list[str] | None,
    sort: str,
    order: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Daftar indikator publik berhalaman."""
    daftar, total = repo_indikator.cari(
        session,
        q=q,
        kategori=kategori,
        kelompok=kelompok,
        tim=tim,
        status_metadata=status_metadata,
        sort=sort,
        order=order,
        page=page,
        page_size=page_size,
    )
    return {
        "data": [ringkas(item) for item in daftar],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def detail(session: Session, indikator: Indikator) -> dict[str, Any]:
    """Ringkasan capaian + seri nilai provinsi + metadata teknis."""
    id_indikator = indikator.id_indikator
    muatan = svc_capaian.muatan(session, indikator)
    muatan["nilai"] = [
        {
            "tahun": baris.tahun,
            "jenis": baris.jenis,
            "nilai": baris.nilai,
            # Nama lama dipertahankan sampai frontend diselaraskan.
            "sumber_sheet": baris.sumber,
        }
        for baris in repo_nilai.seri(session, id_indikator, KODE_PROVINSI)
    ]
    metadata = repo_indikator.ambil_metadata(session, id_indikator)
    muatan["metadata"] = (
        None
        if metadata is None
        else {
            "definisi": metadata.definisi,
            "rumus_mentah": metadata.rumus_mentah,
            "interpretasi": metadata.interpretasi,
            "sumber_data": metadata.sumber_data,
            "frekuensi": metadata.frekuensi,
            "halaman_sumber": metadata.halaman_sumber,
            "sumber_metadata": metadata.sumber_metadata,
            "perlu_verifikasi_manual": metadata.perlu_verifikasi_manual,
        }
    )
    return muatan


def metadata_lengkap(session: Session, indikator: Indikator) -> dict[str, Any]:
    """Muatan `/beranda-indikator/{id}/metadata`."""
    id_indikator = indikator.id_indikator
    metadata = repo_indikator.ambil_metadata(session, id_indikator)
    isi_metadata = (
        None
        if metadata is None
        else {
            "definisi": metadata.definisi,
            "rumus_mentah": metadata.rumus_mentah,
            "rumus_latex": metadata.rumus_latex,
            "interpretasi": metadata.interpretasi,
            "sumber_data": metadata.sumber_data,
            "frekuensi": metadata.frekuensi,
            "status_metadata": metadata.status_metadata,
            "sumber_metadata": metadata.sumber_metadata,
        }
    )
    # "Tersedia" berarti ada isi yang bermakna, bukan sekadar barisnya ada.
    tersedia = bool(isi_metadata and any(isi_metadata.get(kunci) for kunci in FIELD_METADATA_BERMAKNA))
    return {
        "id_indikator": indikator.id_indikator,
        "kategori": indikator.kategori,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "kelompok": indikator.kelompok,
        "arah_pembangunan": indikator.arah_pembangunan,
        "satuan": indikator.satuan,
        "opd_pengampu": indikator.opd_pengampu,
        "status_ketersediaan": indikator.status_ketersediaan,
        "periode_data": indikator.periode_data,
        "metadata": isi_metadata,
        "metadata_tersedia": tersedia,
        "nilai": [
            {
                "tahun": baris.tahun,
                "jenis": baris.jenis,
                "nilai": baris.nilai,
                "nilai_teks": baris.nilai_teks,
                "satuan_catatan": baris.satuan_catatan,
            }
            for baris in repo_nilai.seri_lengkap(session, id_indikator, KODE_PROVINSI)
        ],
    }


def arah_baik_sah(arah_baik: str) -> bool:
    return arah_baik in tuple(ArahBaik)


def koreksi_arah_baik(
    session: Session,
    indikator: Indikator,
    *,
    arah_baik: str,
    pengguna_id: int | None,
) -> dict[str, Any]:
    """Koreksi arah baik oleh admin, beserta jejak perubahannya."""
    lama = repo_indikator.ubah_arah_baik(indikator, arah_baik)
    repo_tata_kelola.catat_perubahan(
        session,
        pengguna_id=pengguna_id,
        id_indikator=indikator.id_indikator,
        field="arah_baik",
        nilai_lama=lama,
        nilai_baru=arah_baik,
        sumber_perubahan="koreksi_admin",
    )
    session.commit()
    return {"status": "ok", "id_indikator": indikator.id_indikator, "arah_baik": arah_baik}

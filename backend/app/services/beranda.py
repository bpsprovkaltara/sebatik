"""Penyusunan muatan beranda: kartu makro, sasaran visi, dan ketersediaan.

Dipisahkan dari router karena isinya perhitungan, bukan HTTP: memilih tahun
yang ditampilkan, memilih antara angka tahunan dan rilis semester, lalu
menurunkan selisih serta arah perubahannya (backend.md §1.2).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import KODE_PROVINSI, Indikator, JenisNilai
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from . import ketersediaan as svc_ketersediaan
from . import nilai as svc_nilai

STATUS_HANYA_TERVERIFIKASI = "HANYA_TERVERIFIKASI"

# Lima indikator sorotan beranda. Sejak kartu makro berjalan sebagai korsel,
# daftar ini tidak lagi membatasi apa yang tampil — ia hanya menentukan urutan
# tampil pertama. Sisanya diambil dari klasifikasi kelompok_makro di basis data
# dan menyusul di belakangnya.
SOROTAN_MAKRO = ("ISV-001", "IUP-050", "ISV-004", "ISV-005", "IUP-028")

PESAN_TANPA_DATA = "Data belum tersedia pada tahun dipilih"


def urutkan_makro(daftar: list[Indikator]) -> list[Indikator]:
    """Lima sorotan lebih dulu, sisanya mengikuti urutan dari repository."""
    menurut_id = {item.id_indikator: item for item in daftar}
    disorot = [menurut_id[i] for i in SOROTAN_MAKRO if i in menurut_id]
    id_disorot = {item.id_indikator for item in disorot}
    return disorot + [item for item in daftar if item.id_indikator not in id_disorot]


def _kartu_makro(session: Session, indikator: Indikator, wilayah_kode: str, tahun: int) -> dict[str, Any]:
    iid = indikator.id_indikator
    seri = repo_nilai.seri(session, iid, wilayah_kode)
    sekarang = next((x for x in seri if x.tahun == tahun and x.jenis == JenisNilai.REALISASI), None)
    sebelumnya = next((x for x in reversed(seri) if x.tahun < tahun and x.jenis == JenisNilai.REALISASI), None)
    target = next((x for x in seri if x.tahun == tahun and x.jenis == JenisNilai.TARGET), None)

    angka_sekarang = (
        svc_nilai.angka_terakhir(
            sekarang.nilai if sekarang else None,
            sekarang.nilai_teks if sekarang else None,
        )
    )
    angka_sebelumnya = svc_nilai.angka_terakhir(
        sebelumnya.nilai if sebelumnya else None,
        sebelumnya.nilai_teks if sebelumnya else None,
    )
    return {
        "id_indikator": iid,
        "nama_indikator": indikator.nama_indikator,
        "arah_pembangunan": indikator.arah_pembangunan,
        "kode_indikator": indikator.kode_indikator,
        "satuan": indikator.satuan,
        "tahun": tahun,
        "nilai": sekarang.nilai if sekarang else None,
        "nilai_teks": sekarang.nilai_teks if sekarang else None,
        "target": target.nilai if target else None,
        "target_teks": target.nilai_teks if target else None,
        "perubahan": svc_nilai.selisih(angka_sekarang, angka_sebelumnya),
        "arah_perubahan": svc_nilai.arah_perubahan(angka_sekarang, angka_sebelumnya),
        "label_periode": svc_nilai.label_periode_tampil(
            indikator.nama_indikator, sekarang.label_periode, tahun
        ) if sekarang else None,
        "keterangan": PESAN_TANPA_DATA if not sekarang else sekarang.satuan_catatan,
    }


def _kartu_visi(session: Session, indikator: Indikator, wilayah_kode: str, tahun: int) -> dict[str, Any]:
    iid = indikator.id_indikator
    seri = repo_nilai.seri(session, iid, wilayah_kode)
    realisasi = next((x for x in seri if x.tahun == tahun and x.jenis == JenisNilai.REALISASI), None)
    target = next((x for x in seri if x.tahun == tahun and x.jenis == JenisNilai.TARGET), None)
    return {
        "id_indikator": iid,
        "kode_indikator": indikator.kode_indikator,
        "nama_indikator": indikator.nama_indikator,
        "arah_pembangunan": indikator.arah_pembangunan,
        "satuan": indikator.satuan,
        "tahun": tahun,
        "nilai": realisasi.nilai if realisasi else None,
        "nilai_teks": realisasi.nilai_teks if realisasi else None,
        "target": target.nilai if target else None,
        "target_teks": target.nilai_teks if target else None,
        "label_periode": svc_nilai.label_periode_tampil(
            indikator.nama_indikator, realisasi.label_periode, tahun
        ) if realisasi else None,
        "keterangan": PESAN_TANPA_DATA if not realisasi else realisasi.satuan_catatan,
    }


def susun(session: Session, *, tahun: int | None, wilayah_kode: str = KODE_PROVINSI) -> dict[str, Any]:
    """Muatan lengkap `/beranda` untuk satu wilayah dan satu tahun."""
    tahun_asli = repo_nilai.tahun_realisasi_tersedia(session)
    if not tahun_asli:
        # Bentuk respons tetap sama seperti saat ada data; hanya isinya kosong,
        # supaya frontend tidak perlu menangani dua bentuk yang berbeda.
        return {
            "tahun": tahun,
            "wilayah_kode": wilayah_kode,
            "tahun_tersedia": [],
            "indikator_makro": [],
            "sasaran_visi": [],
            "ketersediaan_tahunan": [],
            "ketersediaan_kelompok": svc_ketersediaan.ketersediaan_kelompok(session),
            "status_data": STATUS_HANYA_TERVERIFIKASI,
        }

    tahun_tersedia = sorted(set(tahun_asli) | set(range(2021, 2026)))
    dipilih = tahun if tahun in tahun_tersedia else max(tahun_tersedia)
    return {
        "tahun": dipilih,
        "wilayah_kode": wilayah_kode,
        "tahun_tersedia": tahun_tersedia,
        "indikator_makro": [
            _kartu_makro(session, indikator, wilayah_kode, dipilih)
            for indikator in urutkan_makro(repo_indikator.daftar_makro(session))
        ],
        "sasaran_visi": [
            _kartu_visi(session, indikator, wilayah_kode, dipilih)
            for indikator in repo_indikator.daftar_sasaran_visi(session)
        ],
        "ketersediaan_tahunan": svc_ketersediaan.ketersediaan_tahunan(
            session, tahun_tersedia, wilayah_kode
        ),
        "ketersediaan_kelompok": svc_ketersediaan.ketersediaan_kelompok(session),
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }

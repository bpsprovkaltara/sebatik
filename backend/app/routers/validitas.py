"""Endpoint validitas: status verifikasi dan jejak pembaruan tiap indikator."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..deps import get_session, pengguna_saat_ini
from ..models import KODE_PROVINSI, Peran
from ..repositories import indikator as repo_indikator
from ..repositories import nilai as repo_nilai
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories import wilayah as repo_wilayah
from ..repositories.pengguna import ProfilPengguna

router = APIRouter(prefix="/api/v1", tags=["validitas"])

STATUS_HANYA_TERVERIFIKASI = "HANYA_TERVERIFIKASI"
# Batas aman: sebelumnya endpoint ini mengembalikan seluruh baris tanpa batas.
BATAS_MAKSIMUM = 200


@router.get("/validitas")
def validitas(
    wilayah_kode: str = KODE_PROVINSI,
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(BATAS_MAKSIMUM, ge=1, le=BATAS_MAKSIMUM),
    pengguna: ProfilPengguna = Depends(pengguna_saat_ini),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    wilayah = repo_wilayah.ambil_aktif(session, wilayah_kode)
    if wilayah is None:
        raise HTTPException(422, "Wilayah tidak valid")

    indikator = repo_indikator.daftar_terverifikasi(session)
    if q:
        kunci = q.lower()
        indikator = [
            item
            for item in indikator
            if kunci in (item.nama_indikator or "").lower() or kunci in (item.kode_indikator or "").lower()
        ]
    total = len(indikator)
    halaman = indikator[(page - 1) * page_size : page * page_size]

    boleh_lihat_bukti = pengguna.peran in {Peran.ADMIN, Peran.VERIFIKATOR}
    data = []
    for item in halaman:
        terakhir = repo_nilai.diverifikasi_terakhir(session, item.id_indikator, wilayah_kode)
        usulan = repo_tata_kelola.ambil_usulan(session, terakhir.usulan_id) if terakhir and terakhir.usulan_id else None
        pengusul = repo_tata_kelola.ambil_pengusul(session, usulan.pengusul_id) if usulan else None

        tersedia = terakhir is not None
        diverifikasi_pada = terakhir.diverifikasi_pada if terakhir else None
        if pengusul is not None:
            pembaru, peran_pembaru = pengusul.nama, pengusul.peran
        elif tersedia and wilayah_kode == KODE_PROVINSI:
            # Nilai master provinsi tanpa jejak usulan berasal dari basis data
            # yang dimuat admin, bukan dari alur operator.
            pembaru, peran_pembaru = "Admin Provinsi", Peran.ADMIN.value
        else:
            pembaru, peran_pembaru = None, None

        metadata = repo_indikator.ambil_metadata(session, item.id_indikator)
        metadata_tersedia = bool(
            metadata
            and any(
                (
                    metadata.definisi,
                    metadata.rumus_mentah,
                    metadata.interpretasi,
                    metadata.sumber_data,
                    metadata.frekuensi,
                )
            )
        )
        bukti = repo_tata_kelola.daftar_bukti(session, usulan.id) if usulan else []
        # Operator hanya boleh melihat bukti pada usulannya sendiri.
        boleh = boleh_lihat_bukti or (
            pengguna.peran == Peran.OPERATOR and usulan is not None and usulan.pengusul_id == pengguna.id
        )
        data.append(
            {
                "id_indikator": item.id_indikator,
                "kode_indikator": item.kode_indikator,
                "nama_indikator": item.nama_indikator,
                "satuan": item.satuan,
                "instansi_pengampu": item.opd_pengampu or "Belum ditetapkan",
                "validasi": f"Terverifikasi tanggal {diverifikasi_pada}" if diverifikasi_pada else "Belum diverifikasi",
                "terverifikasi_pada": diverifikasi_pada,
                "update": f"Terakhir update tanggal {diverifikasi_pada} oleh {pembaru}"
                if diverifikasi_pada and pembaru
                else "Belum ada pembaruan",
                "update_oleh": pembaru,
                "peran_update": peran_pembaru,
                "status_indikator": "Proxy"
                if item.is_proxy and tersedia
                else ("Tersedia" if tersedia else "Belum Tersedia"),
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
        )

    return {
        "wilayah": {"kode": wilayah.kode, "nama": wilayah.nama, "tingkat": wilayah.tingkat},
        "wilayah_opsi": [
            {"kode": w.kode, "nama": w.nama, "tingkat": w.tingkat} for w in repo_wilayah.daftar_aktif(session)
        ],
        "data": data,
        "total": total,
        "status_data": STATUS_HANYA_TERVERIFIKASI,
    }

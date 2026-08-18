"""Endpoint unggahan Excel massal: pratinjau diff dan persetujuan."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..deps import get_session, wajib_peran
from ..models import Peran, StatusUnggahan
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories.pengguna import ProfilPengguna
from ..services import unggahan as svc

router = APIRouter(prefix="/api/v1", tags=["unggahan"])

hanya_admin = wajib_peran(Peran.ADMIN)


@router.post("/admin/unggah/pratinjau")
async def pratinjau_unggahan(
    file: UploadFile = File(...),
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    if not svc.berekstensi_xlsx(file.filename):
        raise HTTPException(422, "Hanya file .xlsx")
    isi = await file.read()
    if not svc.ukuran_wajar(len(isi)):
        raise HTTPException(413, "File melebihi 30 MB")

    arsip = svc.arsipkan(isi)
    try:
        svc.periksa_sheet(arsip)
        # Pipeline ETL diimpor di sini, bukan di tingkat modul, agar impor
        # router tidak menyeret openpyxl/pdfplumber pada setiap proses.
        from src.etl.pipeline import run as jalankan_etl

        staging = arsip.with_suffix(".stage.db")
        jalankan_etl(arsip, staging, arsip.with_suffix(".stage.md"))
        diff, _ = svc.susun_diff(session, staging)
    except svc.BerkasTidakValid as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        # Galat pipeline ETL berarti berkasnya tidak dapat diproses, bukan
        # kesalahan server; 422 sudah menjadi kontrak endpoint ini.
        raise HTTPException(422, f"ETL pratinjau gagal: {exc}") from exc

    unggahan = repo_tata_kelola.catat_unggahan(
        session,
        nama_file_asli=file.filename,
        path_arsip=str(arsip),
        checksum_sha256=sha256(isi).hexdigest(),
        status=StatusUnggahan.MENUNGGU_PERSETUJUAN,
        ringkasan_diff=svc.ringkasan_diff_json(diff),
        pengguna_id=admin.id,
    )
    session.commit()
    return {"id": unggahan.id, "diff": diff}


@router.post("/admin/unggah/{unggahan_id}/setujui")
def setujui_unggahan(
    unggahan_id: int,
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    unggahan = repo_tata_kelola.ambil_unggahan_menunggu(session, unggahan_id)
    if unggahan is None:
        raise HTTPException(404, "Unggahan tidak ditemukan")
    try:
        svc.terapkan(session, unggahan, admin.id)
    except svc.BerkasTidakValid as exc:
        raise HTTPException(409, str(exc)) from exc
    session.commit()
    return {"status": "DISETUJUI"}

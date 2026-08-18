"""Endpoint administrasi akun dan audit."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..deps import get_session, wajib_peran
from ..models import KODE_PROVINSI, PERAN, Peran
from ..repositories import pengguna as repo_pengguna
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories import wilayah as repo_wilayah
from ..repositories.pengguna import ProfilPengguna
from ..security import PANJANG_PASSWORD_MINIMUM, hash_password, password_memenuhi_syarat

router = APIRouter(prefix="/api/v1", tags=["admin"])

PESAN_PASSWORD_PENDEK = f"Kata sandi minimal {PANJANG_PASSWORD_MINIMUM} karakter"
hanya_admin = wajib_peran(Peran.ADMIN)


@router.post("/admin/pengguna")
def buat_pengguna(
    username: str = Form(...),
    nama: str = Form(...),
    password: str = Form(...),
    peran: str = Form(...),
    wilayah_kode: str | None = Form(None),
    tim_pjk: str | None = Form(None),
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if peran not in tuple(PERAN):
        raise HTTPException(422, "Peran tidak valid")
    if peran in {Peran.OPERATOR, Peran.VERIFIKATOR} and not repo_wilayah.ada_dan_aktif(session, wilayah_kode):
        raise HTTPException(422, "Wilayah wajib dan harus aktif")
    if peran == Peran.VERIFIKATOR and wilayah_kode != KODE_PROVINSI:
        raise HTTPException(422, "Verifikator hanya dapat ditempatkan pada Provinsi Kalimantan Utara")
    if not password_memenuhi_syarat(password):
        raise HTTPException(422, PESAN_PASSWORD_PENDEK)

    repo_pengguna.buat(
        session,
        username=username,
        nama=nama,
        password_hash=hash_password(password),
        peran=peran,
        tim_pjk=tim_pjk,
        wilayah_kode=wilayah_kode,
    )
    try:
        session.commit()
    except IntegrityError as exc:
        # Hanya pelanggaran keunikan yang berarti "username sudah dipakai";
        # galat lain tidak boleh disamarkan menjadi 409.
        session.rollback()
        raise HTTPException(409, "Username sudah digunakan") from exc
    return {"status": "DIBUAT", "username": username}


@router.get("/admin/pengguna")
def daftar_pengguna(
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return {
        "data": [
            {
                "id": akun.id,
                "username": akun.username,
                "nama": akun.nama,
                "peran": akun.peran,
                "wilayah_kode": akun.wilayah_kode,
                "wilayah": nama_wilayah,
                "tim_pjk": akun.tim_pjk,
                "aktif": akun.aktif,
                "harus_ganti_password": akun.harus_ganti_password,
            }
            for akun, nama_wilayah in repo_pengguna.daftar_dengan_wilayah(session)
        ]
    }


@router.patch("/admin/pengguna/{pengguna_id}/status")
def ubah_status_pengguna(
    pengguna_id: int,
    aktif: bool = Form(...),
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if pengguna_id == admin.id and not aktif:
        raise HTTPException(422, "Admin tidak dapat menonaktifkan akunnya sendiri")
    akun = repo_pengguna.ambil(session, pengguna_id)
    if akun is None:
        raise HTTPException(404, "Pengguna tidak ditemukan")

    akun.aktif = aktif
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=admin.id,
        aksi="UBAH_STATUS_AKUN",
        objek_tipe="pengguna",
        objek_id=str(pengguna_id),
        detail={"aktif": aktif},
    )
    session.commit()
    return {"status": "AKTIF" if aktif else "NONAKTIF"}


@router.post("/admin/pengguna/{pengguna_id}/reset-password")
def reset_password(
    pengguna_id: int,
    password_baru: str = Form(...),
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    if not password_memenuhi_syarat(password_baru):
        raise HTTPException(422, PESAN_PASSWORD_PENDEK)
    akun = repo_pengguna.ambil(session, pengguna_id)
    if akun is None:
        raise HTTPException(404, "Pengguna tidak ditemukan")

    # Reset oleh admin selalu memaksa ganti sandi pada login berikutnya.
    repo_pengguna.ganti_password(akun, hash_password(password_baru), wajib_ganti=True)
    repo_tata_kelola.catat_aktivitas(
        session,
        pengguna_id=admin.id,
        aksi="RESET_PASSWORD",
        objek_tipe="pengguna",
        objek_id=str(pengguna_id),
        detail="Kata sandi direset oleh admin",
    )
    session.commit()
    return {"status": "PASSWORD_DIRESET"}


@router.get("/admin/log")
def log_audit(
    admin: ProfilPengguna = Depends(hanya_admin),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return {"data": repo_tata_kelola.daftar_log_perubahan(session)}

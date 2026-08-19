"""Endpoint alur usulan nilai: kirim, tinjau bukti, dan verifikasi."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..deps import get_session, id_terautentikasi, wajib_peran
from ..models import Peran
from ..repositories import indikator as repo_indikator
from ..repositories import tata_kelola as repo_tata_kelola
from ..repositories import wilayah as repo_wilayah
from ..repositories.pengguna import ProfilPengguna
from ..schemas.umum import StatusResponse
from ..schemas.usulan import DaftarBuktiResponse, DaftarUsulanResponse, UsulanDibuatResponse
from ..services import bukti as svc_bukti
from ..services import verifikasi as svc_verifikasi

router = APIRouter(prefix="/api/v1", tags=["usulan"])

boleh_mengusulkan = wajib_peran(Peran.ADMIN, Peran.OPERATOR)
boleh_melihat = wajib_peran(Peran.ADMIN, Peran.OPERATOR, Peran.VERIFIKATOR)
boleh_memutuskan = wajib_peran(Peran.ADMIN, Peran.VERIFIKATOR)


@router.post("/admin/usulan", response_model=UsulanDibuatResponse)
async def kirim_usulan(
    id_indikator: str = Form(...),
    tahun: int = Form(...),
    jenis: str = Form(...),
    nilai: float = Form(...),
    periode: int | None = Form(None),
    sumber: str = Form(...),
    catatan: str | None = Form(None),
    wilayah_kode: str | None = Form(None),
    bukti: list[UploadFile] | None = File(None),
    pengguna: ProfilPengguna = Depends(boleh_mengusulkan),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    penolakan = svc_verifikasi.periksa_pengusulan(
        peran=pengguna.peran,
        jenis=jenis,
        wilayah_operator=pengguna.wilayah_kode,
        wilayah_diminta=wilayah_kode,
    )
    if penolakan:
        raise HTTPException(penolakan.kode, penolakan.pesan)
    if not repo_indikator.ada(session, id_indikator):
        raise HTTPException(404, "Indikator tidak ditemukan")

    lingkup = svc_verifikasi.lingkup_wilayah(
        peran=pengguna.peran,
        wilayah_operator=pengguna.wilayah_kode,
        wilayah_diminta=wilayah_kode,
    )
    if not repo_wilayah.ada_dan_aktif(session, lingkup):
        raise HTTPException(422, "Wilayah tidak valid")
    if not svc_verifikasi.periode_sah(periode):
        raise HTTPException(422, "Periode semester harus 1 atau 2")

    lampiran = [
        svc_bukti.Lampiran(nama_file=berkas.filename, isi=await berkas.read(), mime_type=berkas.content_type)
        for berkas in (bukti or [])
    ]
    ditolak = svc_bukti.periksa_lampiran(lampiran)
    if ditolak:
        raise HTTPException(ditolak.kode, ditolak.pesan)

    usulan = svc_verifikasi.ajukan(
        session,
        id_indikator=id_indikator,
        wilayah_kode=lingkup,
        tahun=tahun,
        jenis=jenis,
        periode=periode,
        nilai=nilai,
        sumber=sumber,
        catatan=catatan,
        pengusul_id=id_terautentikasi(pengguna),
        lampiran=lampiran,
    )
    return {
        "status": "MENUNGGU_VERIFIKASI",
        "id": usulan.id,
        "jumlah_bukti": len(lampiran),
    }


@router.get("/admin/usulan", response_model=DaftarUsulanResponse)
def daftar_usulan(
    status: str | None = None,
    pengguna: ProfilPengguna = Depends(boleh_melihat),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    return {
        "data": repo_tata_kelola.daftar_usulan(
            session,
            status=status,
            # Operator hanya melihat usulannya sendiri.
            pengusul_id=pengguna.id if pengguna.peran == Peran.OPERATOR else None,
            # Verifikator di luar provinsi tidak berwenang memutuskan apa pun.
            kosongkan=pengguna.peran == Peran.VERIFIKATOR and pengguna.wilayah_kode != svc_verifikasi.KODE_PROVINSI,
        )
    }


def _usulan_dapat_diakses(session: Session, pengguna: ProfilPengguna, usulan_id: int):
    usulan = repo_tata_kelola.ambil_usulan(session, usulan_id)
    if usulan is None:
        raise HTTPException(404, "Usulan tidak ditemukan")
    if pengguna.peran == Peran.OPERATOR and usulan.pengusul_id != pengguna.id:
        raise HTTPException(403, "Bukti bukan milik usulan Anda")
    return usulan


@router.get("/admin/usulan/{usulan_id}/bukti", response_model=DaftarBuktiResponse)
def daftar_bukti(
    usulan_id: int,
    pengguna: ProfilPengguna = Depends(boleh_melihat),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    _usulan_dapat_diakses(session, pengguna, usulan_id)
    bukti = repo_tata_kelola.daftar_bukti(session, usulan_id)
    return {"data": svc_bukti.ringkas(bukti, sertakan_checksum=True)}


@router.get("/admin/usulan/{usulan_id}/bukti/{bukti_id}")
def lihat_bukti(
    usulan_id: int,
    bukti_id: int,
    pengguna: ProfilPengguna = Depends(boleh_melihat),
    session: Session = Depends(get_session),
) -> FileResponse:
    _usulan_dapat_diakses(session, pengguna, usulan_id)
    bukti = repo_tata_kelola.ambil_bukti(session, usulan_id, bukti_id)
    if bukti is None:
        raise HTTPException(404, "Bukti dukung tidak ditemukan")

    path = svc_bukti.path_boleh_dibaca(bukti.path_file)
    if path is None or not path.exists():
        raise HTTPException(410, "File bukti dukung tidak tersedia di penyimpanan")
    return FileResponse(
        path,
        media_type=bukti.mime_type or "application/octet-stream",
        filename=bukti.nama_file,
        content_disposition_type="inline",
    )


@router.post("/admin/usulan/{usulan_id}/verifikasi", response_model=StatusResponse)
def verifikasi_usulan(
    usulan_id: int,
    keputusan: str = Form(...),
    alasan: str | None = Form(None),
    pengguna: ProfilPengguna = Depends(boleh_memutuskan),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    usulan = repo_tata_kelola.ambil_usulan_menunggu(session, usulan_id)
    if usulan is None:
        raise HTTPException(404, "Usulan tidak ditemukan")

    verifikator_id = id_terautentikasi(pengguna)
    penolakan = svc_verifikasi.periksa_keputusan(
        keputusan=keputusan,
        alasan=alasan,
        peran_verifikator=pengguna.peran,
        wilayah_verifikator=pengguna.wilayah_kode,
        pengusul_id=usulan.pengusul_id,
        verifikator_id=verifikator_id,
    )
    if penolakan:
        raise HTTPException(penolakan.kode, penolakan.pesan)

    svc_verifikasi.putuskan(session, usulan, keputusan=keputusan, alasan=alasan, verifikator_id=verifikator_id)
    return {"status": keputusan}

"""Query terhadap tabel alur tata kelola: usulan, bukti, log, unggahan."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from ..models import (
    BuktiDukung,
    LogAktivitas,
    LogPerubahan,
    Pengguna,
    StatusVerifikasi,
    UnggahanExcel,
    UsulanNilai,
    Wilayah,
)

# Batas aman daftar log; tanpa ini panel admin memuat seluruh riwayat.
BATAS_LOG = 500


def ambil_usulan(session: Session, usulan_id: int) -> UsulanNilai | None:
    return session.get(UsulanNilai, usulan_id)


def ambil_usulan_menunggu(session: Session, usulan_id: int) -> UsulanNilai | None:
    stmt = select(UsulanNilai).where(UsulanNilai.id == usulan_id, UsulanNilai.status == StatusVerifikasi.MENUNGGU)
    return session.scalars(stmt).first()


def daftar_usulan(
    session: Session,
    *,
    status: str | None = None,
    pengusul_id: int | None = None,
    kosongkan: bool = False,
) -> list[dict[str, Any]]:
    """Daftar usulan beserta nama pengusul, verifikator, wilayah, jumlah bukti.

    `kosongkan=True` dipakai untuk verifikator non-provinsi yang secara aturan
    tidak berhak melihat antrean apa pun.
    """
    if kosongkan:
        return []

    pengusul = aliased(Pengguna)
    verifikator = aliased(Pengguna)
    jumlah_bukti = (
        select(func.count()).select_from(BuktiDukung).where(BuktiDukung.usulan_id == UsulanNilai.id).scalar_subquery()
    )

    stmt = (
        select(
            UsulanNilai,
            pengusul.nama.label("pengusul"),
            pengusul.peran.label("peran_pengusul"),
            Wilayah.nama.label("wilayah"),
            verifikator.nama.label("verifikator"),
            jumlah_bukti.label("jumlah_bukti"),
        )
        .join(pengusul, pengusul.id == UsulanNilai.pengusul_id)
        .join(verifikator, verifikator.id == UsulanNilai.verifikator_id, isouter=True)
        .join(Wilayah, Wilayah.kode == UsulanNilai.wilayah_kode, isouter=True)
        .order_by(UsulanNilai.dibuat_pada.desc())
    )
    if status:
        stmt = stmt.where(UsulanNilai.status == status)
    if pengusul_id is not None:
        stmt = stmt.where(UsulanNilai.pengusul_id == pengusul_id)

    hasil = []
    for baris in session.execute(stmt):
        usulan: UsulanNilai = baris[0]
        hasil.append(
            {
                "id": usulan.id,
                "id_indikator": usulan.id_indikator,
                "wilayah_kode": usulan.wilayah_kode,
                "tahun": usulan.tahun,
                "jenis": usulan.jenis,
                "periode": usulan.periode,
                "nilai": usulan.nilai,
                "sumber": usulan.sumber,
                "catatan": usulan.catatan,
                "status": usulan.status,
                "pengusul_id": usulan.pengusul_id,
                "verifikator_id": usulan.verifikator_id,
                "alasan_verifikasi": usulan.alasan_verifikasi,
                "dibuat_pada": usulan.dibuat_pada,
                "dikirim_pada": usulan.dikirim_pada,
                "diverifikasi_pada": usulan.diverifikasi_pada,
                "pengusul": baris.pengusul,
                "peran_pengusul": baris.peran_pengusul,
                "wilayah": baris.wilayah,
                "verifikator": baris.verifikator,
                "jumlah_bukti": baris.jumlah_bukti,
            }
        )
    return hasil


def buat_usulan(session: Session, **kolom: Any) -> UsulanNilai:
    usulan = UsulanNilai(**kolom)
    session.add(usulan)
    session.flush()  # dibutuhkan agar id tersedia untuk penamaan folder bukti
    return usulan


def putuskan_usulan(
    usulan: UsulanNilai, *, keputusan: str, alasan: str | None, verifikator_id: int, waktu: Any
) -> None:
    usulan.status = keputusan
    usulan.verifikator_id = verifikator_id
    usulan.alasan_verifikasi = alasan
    usulan.diverifikasi_pada = waktu


def daftar_bukti(session: Session, usulan_id: int) -> list[BuktiDukung]:
    stmt = select(BuktiDukung).where(BuktiDukung.usulan_id == usulan_id).order_by(BuktiDukung.id)
    return list(session.scalars(stmt))


def ambil_bukti(session: Session, usulan_id: int, bukti_id: int) -> BuktiDukung | None:
    stmt = select(BuktiDukung).where(BuktiDukung.id == bukti_id, BuktiDukung.usulan_id == usulan_id)
    return session.scalars(stmt).first()


def catat_bukti(session: Session, **kolom: Any) -> BuktiDukung:
    bukti = BuktiDukung(**kolom)
    session.add(bukti)
    return bukti


def catat_perubahan(
    session: Session,
    *,
    pengguna_id: int | None,
    id_indikator: str | None,
    field: str,
    nilai_lama: str | None,
    nilai_baru: str | None,
    sumber_perubahan: str,
    referensi_id: str | None = None,
    catatan: str | None = None,
) -> LogPerubahan:
    log = LogPerubahan(
        pengguna_id=pengguna_id,
        id_indikator=id_indikator,
        field=field,
        nilai_lama=nilai_lama,
        nilai_baru=nilai_baru,
        sumber_perubahan=sumber_perubahan,
        referensi_id=referensi_id,
        catatan=catatan,
    )
    session.add(log)
    return log


def catat_aktivitas(
    session: Session,
    *,
    pengguna_id: int | None,
    aksi: str,
    objek_tipe: str | None = None,
    objek_id: str | None = None,
    detail: dict[str, Any] | str | None = None,
) -> LogAktivitas:
    log = LogAktivitas(
        pengguna_id=pengguna_id,
        aksi=aksi,
        objek_tipe=objek_tipe,
        objek_id=objek_id,
        detail=json.dumps(detail, ensure_ascii=False) if isinstance(detail, dict) else detail,
    )
    session.add(log)
    return log


def daftar_log_perubahan(session: Session, batas: int = BATAS_LOG) -> list[dict[str, Any]]:
    stmt = (
        select(LogPerubahan, Pengguna.username)
        .join(Pengguna, Pengguna.id == LogPerubahan.pengguna_id, isouter=True)
        .order_by(LogPerubahan.waktu.desc())
        .limit(batas)
    )
    return [
        {
            "id": log.id,
            "waktu": log.waktu,
            "pengguna_id": log.pengguna_id,
            "id_indikator": log.id_indikator,
            "field": log.field,
            "nilai_lama": log.nilai_lama,
            "nilai_baru": log.nilai_baru,
            "sumber_perubahan": log.sumber_perubahan,
            "referensi_id": log.referensi_id,
            "catatan": log.catatan,
            "username": username,
        }
        for log, username in session.execute(stmt)
    ]


def ambil_unggahan_menunggu(session: Session, unggahan_id: int) -> UnggahanExcel | None:
    stmt = select(UnggahanExcel).where(UnggahanExcel.id == unggahan_id, UnggahanExcel.status == "MENUNGGU_PERSETUJUAN")
    return session.scalars(stmt).first()


def catat_unggahan(session: Session, **kolom: Any) -> UnggahanExcel:
    unggahan = UnggahanExcel(**kolom)
    session.add(unggahan)
    session.flush()
    return unggahan


def ambil_pengusul(session: Session, pengguna_id: int | None) -> Pengguna | None:
    """Akun pengusul sebuah usulan, untuk menampilkan nama pembaru data."""
    return session.get(Pengguna, pengguna_id) if pengguna_id else None

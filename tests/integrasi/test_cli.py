"""Tes perintah seed: idempoten dan tidak pernah menyetel ulang sandi."""

from __future__ import annotations

import pytest

from backend.app.cli import (
    OPERATOR_PER_WILAYAH,
    PANJANG_SANDI_SEED,
    WILAYAH_KALTARA,
    pastikan_wilayah,
    sandi_acak,
    seed_akun,
)
from backend.app.repositories import pengguna as repo_pengguna
from backend.app.security import verifikasi_password


def test_sandi_acak_panjang_dan_tidak_berulang():
    satu, dua = sandi_acak(), sandi_acak()
    assert len(satu) == PANJANG_SANDI_SEED
    assert satu != dua


def test_seed_membuat_admin_dan_operator_tiap_wilayah(session):
    pastikan_wilayah(session)
    baru = seed_akun(session)

    diharapkan = 1 + len(WILAYAH_KALTARA) * OPERATOR_PER_WILAYAH
    assert len(baru) == diharapkan
    username = {nama for nama, _ in baru}
    assert "admin" in username
    assert "operator.6501.1" in username


def test_sandi_yang_dicetak_benar_benar_dapat_dipakai(session):
    pastikan_wilayah(session)
    baru = dict(seed_akun(session))
    akun = repo_pengguna.ambil_untuk_login(session, "admin")
    assert verifikasi_password(baru["admin"], akun.password_hash)


def test_seluruh_akun_seed_wajib_ganti_sandi(session):
    pastikan_wilayah(session)
    seed_akun(session)
    for akun, _ in repo_pengguna.daftar_dengan_wilayah(session):
        assert akun.harus_ganti_password is True


def test_menjalankan_ulang_tidak_membuat_akun_baru(session):
    pastikan_wilayah(session)
    seed_akun(session)
    assert seed_akun(session) == []


def test_menjalankan_ulang_tidak_mengubah_sandi_yang_ada(session):
    """Seed ulang saat pemasangan tidak boleh mengunci pengguna yang aktif."""
    pastikan_wilayah(session)
    seed_akun(session)
    akun = repo_pengguna.ambil_untuk_login(session, "admin")
    hash_semula = akun.password_hash

    seed_akun(session)
    assert repo_pengguna.ambil_untuk_login(session, "admin").password_hash == hash_semula


def test_wilayah_sudah_terisi_migrasi(session):
    """Migrasi Alembic sudah menanam wilayah; seed tidak menduplikasinya."""
    assert pastikan_wilayah(session) == 0


@pytest.mark.parametrize("kode,nama", [(k, n) for k, n, _, _ in WILAYAH_KALTARA])
def test_operator_terhubung_ke_wilayahnya(session, kode: str, nama: str):
    pastikan_wilayah(session)
    seed_akun(session)
    akun = repo_pengguna.ambil_untuk_login(session, f"operator.{kode}.1")
    assert akun.wilayah_kode == kode
    assert nama in akun.nama

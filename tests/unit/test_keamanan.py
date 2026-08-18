"""Unit test lapisan keamanan: token, kata sandi, pembatas laju, path bukti."""

from __future__ import annotations

from datetime import UTC
from pathlib import Path

import pytest

from backend.app import security
from backend.app.services import bukti as svc_bukti
from backend.app.services.pembatas import PembatasLaju, kunci_percobaan

# --- kata sandi ------------------------------------------------------------


def test_hash_berbeda_tiap_kali_tetapi_tetap_terverifikasi():
    """Argon2 memakai salt acak; dua hash sandi sama tidak boleh identik."""
    satu = security.hash_password("kata-sandi-panjang-1")
    dua = security.hash_password("kata-sandi-panjang-1")
    assert satu != dua
    assert security.verifikasi_password("kata-sandi-panjang-1", satu)
    assert security.verifikasi_password("kata-sandi-panjang-1", dua)


def test_password_salah_ditolak():
    hash_tersimpan = security.hash_password("kata-sandi-panjang-1")
    assert not security.verifikasi_password("kata-sandi-panjang-2", hash_tersimpan)


def test_kebijakan_panjang_minimum():
    assert security.PANJANG_PASSWORD_MINIMUM == 12
    assert security.password_memenuhi_syarat("a" * 12)
    assert not security.password_memenuhi_syarat("a" * 11)


# --- token -----------------------------------------------------------------


def test_token_membawa_subjek_dan_peran():
    muatan = security.baca_token(security.buat_token(7, "ADMIN"))
    assert muatan["sub"] == "7"
    assert muatan["peran"] == "ADMIN"
    assert {"iat", "exp"} <= muatan.keys()


def test_token_kedaluwarsa_ditolak(monkeypatch):
    from datetime import datetime, timedelta

    import jwt

    kedaluwarsa = datetime.now(UTC) - timedelta(hours=1)
    token = jwt.encode(
        {"sub": "1", "peran": "ADMIN", "exp": kedaluwarsa},
        security.settings.secret_key,
        algorithm=security.ALGORITMA,
    )
    with pytest.raises(security.TokenTidakValid):
        security.baca_token(token)


def test_token_dengan_rahasia_lain_ditolak():
    import jwt

    token = jwt.encode({"sub": "1"}, "rahasia-yang-berbeda-sekali", algorithm="HS256")
    with pytest.raises(security.TokenTidakValid):
        security.baca_token(token)


def test_token_sampah_ditolak():
    with pytest.raises(security.TokenTidakValid):
        security.baca_token("bukan-token")


# --- pembatas laju ---------------------------------------------------------


def test_pembatas_mengizinkan_sampai_batas_lalu_menolak():
    pembatas = PembatasLaju(maksimum=3, jendela_detik=60)
    for _ in range(3):
        assert pembatas.periksa("a", sekarang=100.0).diizinkan
    keputusan = pembatas.periksa("a", sekarang=100.0)
    assert keputusan.diizinkan is False
    assert keputusan.sisa_detik > 0


def test_pembatas_pulih_setelah_jendela_lewat():
    pembatas = PembatasLaju(maksimum=2, jendela_detik=60)
    pembatas.periksa("a", sekarang=0.0)
    pembatas.periksa("a", sekarang=1.0)
    assert not pembatas.periksa("a", sekarang=2.0).diizinkan
    assert pembatas.periksa("a", sekarang=61.5).diizinkan


def test_pembatas_terpisah_per_kunci():
    pembatas = PembatasLaju(maksimum=1, jendela_detik=60)
    assert pembatas.periksa("a", sekarang=0.0).diizinkan
    assert pembatas.periksa("b", sekarang=0.0).diizinkan
    assert not pembatas.periksa("a", sekarang=0.0).diizinkan


def test_pembatas_dilupakan_setelah_berhasil():
    pembatas = PembatasLaju(maksimum=1, jendela_detik=60)
    pembatas.periksa("a", sekarang=0.0)
    pembatas.lupakan("a")
    assert pembatas.periksa("a", sekarang=0.0).diizinkan


def test_kunci_menggabungkan_ip_dan_username():
    """Penyerang dari IP lain tidak boleh dapat mengunci akun orang."""
    assert kunci_percobaan("10.0.0.1", "Admin") == kunci_percobaan("10.0.0.1", "admin")
    assert kunci_percobaan("10.0.0.1", "admin") != kunci_percobaan("10.0.0.2", "admin")
    assert kunci_percobaan(None, "admin").startswith("tidak-diketahui")


# --- path bukti ------------------------------------------------------------


def test_path_di_dalam_direktori_bukti_diizinkan(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_bukti.settings, "evidence_dir", tmp_path)
    berkas = tmp_path / "5" / "bukti.pdf"
    berkas.parent.mkdir()
    berkas.write_bytes(b"x")
    assert svc_bukti.path_boleh_dibaca(str(berkas)) == berkas.resolve()


def test_path_di_luar_direktori_bukti_ditolak(tmp_path, monkeypatch):
    """Path absolut tersimpan tidak boleh menjadi jalan ke berkas lain."""
    monkeypatch.setattr(svc_bukti.settings, "evidence_dir", tmp_path / "bukti")
    (tmp_path / "bukti").mkdir()
    luar = tmp_path / "rahasia.env"
    luar.write_text("SECRET=1", encoding="utf-8")
    assert svc_bukti.path_boleh_dibaca(str(luar)) is None


def test_path_traversal_ditolak(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_bukti.settings, "evidence_dir", tmp_path / "bukti")
    (tmp_path / "bukti").mkdir()
    assert svc_bukti.path_boleh_dibaca(str(tmp_path / "bukti" / ".." / "etc")) is None


def test_nama_berkas_unggahan_tidak_dapat_menembus_direktori(tmp_path, monkeypatch):
    monkeypatch.setattr(svc_bukti.settings, "evidence_dir", tmp_path)
    siap = svc_bukti.simpan(9, "../../../etc/passwd", b"isi", "application/pdf")
    assert siap.path_file.parent == tmp_path / "9"
    assert siap.path_file.name.endswith("passwd")
    assert ".." not in str(siap.path_file)
    # Nama asli tetap dicatat apa adanya untuk keperluan audit.
    assert siap.nama_file == "../../../etc/passwd"


def test_format_bukti_dibatasi():
    assert svc_bukti.format_didukung("application/pdf")
    assert svc_bukti.format_didukung("image/png")
    assert not svc_bukti.format_didukung("application/x-msdownload")
    assert not svc_bukti.format_didukung(None)


def test_checksum_dihitung_dari_isi(tmp_path, monkeypatch):
    from hashlib import sha256

    monkeypatch.setattr(svc_bukti.settings, "evidence_dir", tmp_path)
    siap = svc_bukti.simpan(1, "a.pdf", b"halo", "application/pdf")
    assert siap.checksum_sha256 == sha256(b"halo").hexdigest()
    assert siap.ukuran == 4


# --- header keamanan -------------------------------------------------------


def test_direktori_bukti_bawaan_di_bawah_data_processed():
    """Bukti tidak boleh tercecer di luar direktori data aplikasi."""
    from backend.app.config import DEFAULT_DB_PATH, Settings

    assert Settings(_env_file=None).evidence_dir == Path(DEFAULT_DB_PATH).parent / "bukti-dukung"

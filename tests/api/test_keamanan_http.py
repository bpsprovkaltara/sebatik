"""Tes keamanan pada tingkat HTTP: header, pembatas laju, dan kebocoran data."""

from __future__ import annotations

import pytest

from backend.app.services.pembatas import pembatas_login

from .conftest import SANDI_ADMIN


@pytest.fixture(autouse=True)
def bersihkan_pembatas():
    """Hitungan percobaan tidak boleh bocor antar-tes."""
    pembatas_login.kosongkan()
    yield
    pembatas_login.kosongkan()


def test_header_keamanan_terpasang_di_semua_respons(client):
    response = client.get("/api/v1/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_hsts_tidak_dipasang_pada_http(client):
    """HSTS di atas HTTP diabaikan peramban dan mengunci pengembangan lokal."""
    assert "Strict-Transport-Security" not in client.get("/api/v1/health").headers


def test_percobaan_masuk_dibatasi(client):
    salah = {"username": "admin", "password": "sandi-salah-sekali"}
    kode = [client.post("/api/v1/auth/login", data=salah).status_code for _ in range(6)]
    assert kode[:5] == [401] * 5
    assert kode[5] == 429


def test_respons_429_memberi_tahu_kapan_boleh_mencoba_lagi(client):
    salah = {"username": "operator.6501.1", "password": "sandi-salah-sekali"}
    for _ in range(5):
        client.post("/api/v1/auth/login", data=salah)
    response = client.post("/api/v1/auth/login", data=salah)
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0


def test_masuk_berhasil_mengosongkan_jatah(client):
    """Pengguna sah tidak boleh terkunci gara-gara salah ketik beberapa kali."""
    for _ in range(4):
        client.post("/api/v1/auth/login", data={"username": "admin", "password": "salah-sekali-lah"})
    benar = {"username": "admin", "password": SANDI_ADMIN}
    assert client.post("/api/v1/auth/login", data=benar).status_code == 200
    # Jatah kembali penuh setelah berhasil.
    assert client.post("/api/v1/auth/login", data=benar).status_code == 200


def test_pembatas_terpisah_antar_username(client):
    for _ in range(6):
        client.post("/api/v1/auth/login", data={"username": "korban", "password": "xxxxxxxxxxxx"})
    lain = client.post("/api/v1/auth/login", data={"username": "admin", "password": "sandi-salah-lain"})
    assert lain.status_code == 401


def test_respons_tidak_membocorkan_hash_kata_sandi(client, auth):
    for path in ("/api/v1/auth/saya", "/api/v1/admin/pengguna"):
        isi = client.get(path, headers=auth).text
        assert "password_hash" not in isi
        assert "$argon2" not in isi


def test_pesan_galat_masuk_tidak_membedakan_username_dan_sandi(client):
    tidak_ada = client.post("/api/v1/auth/login", data={"username": "hantu", "password": "apa-saja-lah-ini"})
    salah_sandi = client.post("/api/v1/auth/login", data={"username": "admin", "password": "salah-sekali-lah"})
    assert tidak_ada.status_code == salah_sandi.status_code == 401
    assert tidak_ada.json()["detail"] == salah_sandi.json()["detail"]


def test_endpoint_admin_menolak_tanpa_token(client):
    for path in ("/api/v1/admin/pengguna", "/api/v1/admin/log"):
        assert client.get(path).status_code == 403


def test_bukti_dukung_tidak_dapat_diakses_tanpa_peran(client):
    assert client.get("/api/v1/admin/usulan/1/bukti").status_code == 403

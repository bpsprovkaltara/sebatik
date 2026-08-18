"""Tes kontrak API — garis dasar anti-regresi selama refactoring.

Tes ini sengaja memeriksa **bentuk** respons (kunci yang ada dan tipenya),
bukan nilainya, sehingga tetap hijau ketika data berubah tetapi langsung merah
ketika pemindahan endpoint ke router/service/repository mengubah kontrak publik
yang dipakai frontend.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

KODE_PROVINSI = "65"
INDIKATOR_MASTER = "ISV-001"
INDIKATOR_LEGACY = "ISV-04"


def _json(path: str, **kwargs):
    response = client.get(path, **kwargs)
    assert response.status_code == 200, f"{path} -> {response.status_code}"
    return response.json()


def _token_admin() -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Sebatik-Ganti-Segera-2026!"},
    )
    assert response.status_code == 200, "akun seed admin harus ada untuk tes kontrak"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token_admin()}"}


# --- endpoint publik -------------------------------------------------------


def test_health():
    assert _json("/api/v1/health") == {"status": "ok"}


def test_indikator_paginasi():
    body = _json("/api/v1/indikator?page_size=2")
    assert {"data", "total", "page", "page_size"} <= body.keys()
    assert isinstance(body["total"], int)
    assert len(body["data"]) <= 2
    baris = body["data"][0]
    assert {
        "id_indikator",
        "nama_indikator",
        "kategori",
        "kelompok",
        "satuan",
        "tim_pjk",
        "opd_penanggung_jawab",
        "status_metadata",
        "tahun_terakhir",
        "is_proxy",
    } == baris.keys()


def test_beranda_provinsi():
    body = _json("/api/v1/beranda")
    assert {
        "tahun",
        "wilayah_kode",
        "tahun_tersedia",
        "indikator_makro",
        "sasaran_visi",
        "ketersediaan_kelompok",
        "status_data",
    } <= body.keys()
    assert body["wilayah_kode"] == KODE_PROVINSI
    assert body["status_data"] == "HANYA_TERVERIFIKASI"
    makro = body["indikator_makro"][0]
    assert {
        "id_indikator",
        "nama_indikator",
        "tahun",
        "nilai",
        "target",
        "perubahan",
        "arah_perubahan",
        "keterangan",
    } <= makro.keys()
    kelompok = body["ketersediaan_kelompok"][0]
    assert {
        "kode",
        "label",
        "jumlah_kelompok",
        "jumlah_indikator",
        "slot_terisi",
        "slot_total",
        "persentase",
    } == kelompok.keys()
    assert [item["jumlah_kelompok"] for item in body["ketersediaan_kelompok"]] == [5, 8, 17, 45]


@pytest.mark.xfail(
    strict=True,
    reason="Bug model data ganda: beranda_nilai_wilayah tidak punya kolom "
    "satuan_catatan sehingga /beranda untuk kab/kota gagal 500. "
    "Hilang setelah konsolidasi ke satu tabel nilai_indikator (Fase 4).",
)
def test_beranda_wilayah_kabupaten():
    """Beranda harus melayani wilayah kab/kota, bukan hanya provinsi."""
    body = _json("/api/v1/beranda?wilayah_kode=6501")
    assert body["wilayah_kode"] == "6501"
    assert {"indikator_makro", "sasaran_visi", "ketersediaan_kelompok"} <= body.keys()


def test_beranda_menolak_wilayah_asing():
    assert client.get("/api/v1/beranda?wilayah_kode=9999").status_code == 422


def test_indikator_explorer():
    body = _json("/api/v1/indikator-explorer")
    assert {"data", "total_indikator", "status_data"} <= body.keys()
    grup = body["data"][0]
    assert {"kelompok", "jumlah", "indikator"} == grup.keys()


def test_indikator_explorer_detail():
    body = _json(f"/api/v1/indikator-explorer/{INDIKATOR_MASTER}")
    assert {
        "id_indikator",
        "nama_indikator",
        "tahun",
        "tahun_tersedia",
        "series",
        "wilayah",
        "status_data",
        "catatan_wilayah",
    } <= body.keys()
    if body["series"]:
        assert {"tahun", "realisasi", "target", "growth"} <= body["series"][0].keys()
    assert {"kode", "nama", "tingkat", "nilai", "status"} <= body["wilayah"][0].keys()


def test_capaian_explorer():
    body = _json("/api/v1/capaian-explorer")
    assert {"indikator", "kelompok", "wilayah", "status_data"} <= body.keys()


def test_capaian_explorer_detail():
    body = _json(f"/api/v1/capaian-explorer/{INDIKATOR_MASTER}")
    assert {
        "id_indikator",
        "wilayah",
        "tahun",
        "tahun_tersedia",
        "series",
        "projection",
        "target_2045",
        "target_2029",
        "arah_target",
        "progres_2045",
        "progres_2029",
        "gap_2045",
        "gap_2029",
        "kebutuhan_per_tahun",
        "insight",
        "status_data",
    } <= body.keys()
    for nilai in (body["progres_2029"], body["progres_2045"]):
        if nilai is not None:
            assert 0 <= nilai <= 100


def test_insight():
    body = _json("/api/v1/insight")
    assert {
        "tahun_sistem",
        "wilayah",
        "wilayah_opsi",
        "indikator_makro",
        "indikator_aktif",
        "series",
        "perbandingan_wilayah",
        "status_data",
    } <= body.keys()
    assert body["indikator_aktif"]["id_indikator"] == body["indikator_makro"][0]["id_indikator"]


def test_validitas():
    body = _json("/api/v1/validitas")
    assert {"wilayah", "wilayah_opsi", "data", "total", "status_data"} <= body.keys()
    baris = body["data"][0]
    assert {
        "id_indikator",
        "kode_indikator",
        "nama_indikator",
        "satuan",
        "instansi_pengampu",
        "validasi",
        "terverifikasi_pada",
        "update",
        "update_oleh",
        "peran_update",
        "status_indikator",
        "metadata_tersedia",
        "usulan_id",
        "bukti_dukung_jumlah",
        "bukti_dukung",
    } == baris.keys()


def test_metadata_indikator_master():
    body = _json(f"/api/v1/beranda-indikator/{INDIKATOR_MASTER}/metadata")
    assert {"id_indikator", "metadata", "metadata_tersedia", "nilai"} <= body.keys()


def test_wilayah():
    body = _json("/api/v1/wilayah")
    assert {"kode", "nama", "tingkat", "parent_kode"} == body["data"][0].keys()
    assert any(item["kode"] == KODE_PROVINSI for item in body["data"])


def test_capaian():
    body = _json("/api/v1/capaian")
    assert {"data", "total", "arah_bersifat_sementara"} <= body.keys()
    baris = body["data"][0]
    assert {
        "id_indikator",
        "nama_indikator",
        "nilai_terakhir",
        "tahun_terakhir_realisasi",
        "target_tahun_sama",
        "persentase_capaian",
        "status_capaian",
        "tren",
    } <= baris.keys()


def test_capaian_tanpa_data_bukan_nol():
    """Indikator tanpa realisasi tidak boleh dilaporkan sebagai capaian 0%."""
    data = _json("/api/v1/capaian")["data"]
    kosong = [row for row in data if row["nilai_terakhir"] is None]
    assert kosong
    assert all(row["status_capaian"] == "BELUM_ADA_DATA" for row in kosong)
    assert all(row["persentase_capaian"] is None for row in kosong)


def test_detail_indikator_legacy():
    body = _json(f"/api/v1/indikator/{INDIKATOR_LEGACY}/detail")
    assert {"nilai", "metadata", "status_capaian", "arah_baik"} <= body.keys()


def test_analitik():
    selisih = _json(f"/api/v1/analitik/selisih/{INDIKATOR_LEGACY}")
    assert {"id_indikator", "arah_baik", "data"} == selisih.keys()

    peringkat = _json("/api/v1/analitik/peringkat")
    assert {"perbaikan_terbesar", "pemburukan_terbesar"} == peringkat.keys()

    gap = _json(f"/api/v1/analitik/gap/{INDIKATOR_LEGACY}")
    assert "disclaimer" in gap

    multi = _json("/api/v1/analitik/multi?ids=ISV-04&ids=ISV-05")
    assert {"id_indikator", "nama", "seri"} == multi["data"][0].keys()

    korelasi = _json("/api/v1/analitik/korelasi?x=ISV-01&y=ISV-02")
    assert {"n", "pearson", "data", "peringatan"} == korelasi.keys()
    if korelasi["n"] < 4:
        assert korelasi["pearson"] is None


def test_analitik_multi_dibatasi_empat():
    assert client.get("/api/v1/analitik/multi?ids=a&ids=b&ids=c&ids=d&ids=e").status_code == 422


# --- ekspor ----------------------------------------------------------------


@pytest.mark.parametrize(
    "path,prefix",
    [
        ("/api/v1/ekspor.csv", b"\xef\xbb\xbf"),
        ("/api/v1/ekspor.xlsx", b"PK"),
        (f"/api/v1/indikator/{INDIKATOR_LEGACY}/unduh.csv", b"\xef\xbb\xbf"),
        ("/api/v1/download/paket.zip", b"PK"),
    ],
)
def test_ekspor(path: str, prefix: bytes):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content.startswith(prefix)
    assert "attachment" in response.headers["content-disposition"]


# --- autentikasi & admin ---------------------------------------------------


def test_login_dan_profil(auth):
    body = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "Sebatik-Ganti-Segera-2026!"},
    ).json()
    assert {"access_token", "token_type", "peran", "harus_ganti_password"} == body.keys()
    assert body["token_type"] == "bearer"

    saya = _json("/api/v1/auth/saya", headers=auth)
    assert {"id", "username", "nama", "peran"} <= saya.keys()
    assert "password_hash" not in saya


def test_login_salah_401():
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "salah-sekali-1234"})
    assert response.status_code == 401


def test_profil_tamu_tanpa_token():
    assert _json("/api/v1/auth/saya")["peran"] == "PENGUNJUNG"


def test_admin_butuh_peran(auth):
    assert client.get("/api/v1/admin/log").status_code == 403
    assert client.get("/api/v1/admin/pengguna").status_code == 403
    assert client.get("/api/v1/admin/log", headers=auth).status_code == 200

    pengguna = _json("/api/v1/admin/pengguna", headers=auth)
    assert {
        "id",
        "username",
        "nama",
        "peran",
        "wilayah_kode",
        "wilayah",
        "tim_pjk",
        "aktif",
        "harus_ganti_password",
    } == pengguna["data"][0].keys()
    assert all("password_hash" not in row for row in pengguna["data"])


def test_daftar_usulan(auth):
    body = _json("/api/v1/admin/usulan", headers=auth)
    assert "data" in body


def test_endpoint_ketersediaan_lama_sudah_hilang():
    for path in (
        "/api/v1/ringkasan",
        "/api/v1/matriks-ketersediaan",
        "/api/v1/indikator-rawan",
        "/api/v1/tim-pjk",
        "/api/v1/analitik/monev-ketersediaan",
    ):
        assert client.get(path).status_code == 404, path


def test_indikator_publik_tanpa_data_pribadi():
    baris = _json("/api/v1/indikator?page_size=1")["data"][0]
    for terlarang in ("nama_pic", "pic_provinsi", "status_ketersediaan"):
        assert terlarang not in baris

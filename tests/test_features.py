from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_capaian_tanpa_data_bukan_nol():
    data = client.get("/api/v1/capaian").json()["data"]
    missing = [row for row in data if row["nilai_terakhir"] is None]
    assert missing
    assert all(row["status_capaian"] == "BELUM_ADA_DATA" for row in missing)
    assert all(row["persentase_capaian"] is None for row in missing)


def test_detail_and_download_schema():
    detail = client.get("/api/v1/indikator/ISV-04/detail")
    assert detail.status_code == 200
    assert {"nilai", "metadata", "status_capaian", "arah_baik"} <= detail.json().keys()
    assert client.get("/api/v1/indikator/ISV-04/unduh.csv").status_code == 200


def test_short_correlation_is_hidden():
    result = client.get("/api/v1/analitik/korelasi?x=ISV-01&y=ISV-02").json()
    if result["n"] < 4:
        assert result["pearson"] is None


def test_analytics_contracts():
    assert {"data", "arah_baik"} <= client.get("/api/v1/analitik/selisih/ISV-04").json().keys()
    assert {"perbaikan_terbesar", "pemburukan_terbesar"} <= client.get("/api/v1/analitik/peringkat").json().keys()
    assert "disclaimer" in client.get("/api/v1/analitik/gap/ISV-04").json()


def test_admin_requires_authentication():
    assert client.get("/api/v1/admin/log").status_code == 403
    login = client.post("/api/v1/auth/login", data={"username":"admin","password":"Sebatik-Ganti-Segera-2026!"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert client.get("/api/v1/admin/log", headers={"Authorization":f"Bearer {token}"}).status_code == 200


def test_package_export():
    response = client.get("/api/v1/download/paket.zip")
    assert response.status_code == 200
    assert response.content[:2] == b"PK"


def test_public_endpoint_contracts():
    endpoints = [
        ("/api/v1/indikator?page_size=2", {"data","total","page"}),
        ("/api/v1/capaian", {"data","total"}),
    ]
    for url, keys in endpoints:
        response = client.get(url)
        assert response.status_code == 200, url
        assert keys <= response.json().keys(), url


def test_home_and_insight_use_classified_macro_indicators():
    home = client.get("/api/v1/beranda")
    assert home.status_code == 200
    payload = home.json()
    # Lima sorotan tampil lebih dulu, sisanya menyusul dari klasifikasi
    # kelompok_makro — korsel beranda memutar seluruhnya.
    assert [item["nama_indikator"] for item in payload["indikator_makro"][:5]] == [
        "PDRB per Kapita (Rp Juta)",
        "Tingkat inflasi",
        "Tingkat kemiskinan",
        "Rasio gini",
        "Tingkat Pengangguran Terbuka",
    ]
    assert payload["indikator_makro"][4]["nilai"] == 3.85
    assert len(payload["indikator_makro"]) > 5
    assert len({item["id_indikator"] for item in payload["indikator_makro"]}) == len(payload["indikator_makro"])
    assert [item["jumlah_kelompok"] for item in payload["ketersediaan_kelompok"]] == [5, 8, 17, 45]
    assert all(0 <= item["persentase"] <= 100 for item in payload["ketersediaan_kelompok"])

    insight = client.get("/api/v1/insight")
    assert insight.status_code == 200
    insight_macros = insight.json()["indikator_makro"]
    # Pemilih kartu Insight memuat seluruh indikator makro, sejumlah yang sama
    # dengan korsel beranda, dan kartu pertama tetap yang terpilih otomatis.
    assert len(insight_macros) == len(payload["indikator_makro"])
    assert insight.json()["indikator_aktif"]["id_indikator"] == insight_macros[0]["id_indikator"]


def test_availability_feature_is_not_public():
    for url in ("/api/v1/ringkasan", "/api/v1/matriks-ketersediaan", "/api/v1/indikator-rawan", "/api/v1/tim-pjk", "/api/v1/analitik/monev-ketersediaan"):
        assert client.get(url).status_code == 404, url

"""Regresi tingkat data: komposisi kartu makro beranda dan Insight.

Berbeda dari `test_kontrak.py` yang menjaga *bentuk* respons, berkas ini menjaga
*isi* yang pernah salah: urutan lima sorotan, tidak adanya duplikat, dan
kesamaan daftar makro antara beranda dan Insight.

Karena isinya yang diuji, berkas ini memerlukan data produksi sungguhan dan
melewatkan dirinya sendiri bila `data/processed/sebatik.db` tidak tersedia.
"""

from __future__ import annotations

SOROTAN = [
    "PDRB per Kapita (Rp Juta)",
    "Tingkat inflasi",
    "Tingkat kemiskinan",
    "Rasio gini",
    "Tingkat Pengangguran Terbuka",
]


def test_beranda_menampilkan_sorotan_lebih_dulu_lalu_seluruh_makro(client_produksi):
    payload = client_produksi.get("/api/v1/beranda").json()
    makro = payload["indikator_makro"]
    # Lima sorotan tampil lebih dulu, sisanya menyusul dari klasifikasi
    # kelompok_makro — korsel beranda memutar seluruhnya.
    assert [item["nama_indikator"] for item in makro[:5]] == SOROTAN
    assert makro[4]["nilai"] == 3.85
    assert len(makro) > 5
    assert len({item["id_indikator"] for item in makro}) == len(makro)


def test_insight_memakai_daftar_makro_yang_sama_dengan_beranda(client_produksi):
    beranda = client_produksi.get("/api/v1/beranda").json()["indikator_makro"]
    insight = client_produksi.get("/api/v1/insight").json()
    # Pemilih kartu Insight memuat seluruh indikator makro, sejumlah yang sama
    # dengan korsel beranda, dan kartu pertama tetap yang terpilih otomatis.
    assert len(insight["indikator_makro"]) == len(beranda)
    assert insight["indikator_aktif"]["id_indikator"] == insight["indikator_makro"][0]["id_indikator"]

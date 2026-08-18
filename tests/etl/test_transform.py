"""Unit test lapisan transform ETL — fungsi murni, tanpa workbook."""

from __future__ import annotations

import pytest

from src.etl.metadata_pdf import normalize_labels, score_names
from src.etl.transform import (
    bersihkan_teks,
    ekstrak_proxy,
    enum_rpjmd,
    id_indikator,
    kategori_dari_nomor,
    nomor_dalam_kategori,
    parse_angka,
)

ISV_MAKS = 10


@pytest.mark.parametrize(
    "masukan,harapan",
    [
        ("227,10", 227.10),
        ("0.251", 0.251),
        ("1.612,75", 1612.75),
        (" 8,90 ", 8.9),
        (" 1 612,75 ", 1612.75),
        ("1,612.75", 1612.75),
        (12, 12.0),
        (3.5, 3.5),
    ],
)
def test_parse_angka_menerima_format_indonesia_dan_internasional(masukan, harapan):
    assert parse_angka(masukan) == harapan


@pytest.mark.parametrize("masukan", ["Tidak Tersedia", "n.a.", "-", "", None, True])
def test_parse_angka_menolak_yang_bukan_angka(masukan):
    """True sengaja ditolak: bool adalah int di Python, tetapi bukan nilai data."""
    assert parse_angka(masukan) is None


def test_bersihkan_teks_meratakan_spasi():
    assert bersihkan_teks("Nama  \n indikator") == "Nama indikator"
    assert bersihkan_teks("   ") is None
    assert bersihkan_teks(None) is None


def test_id_indikator_dibakukan_dua_digit():
    assert id_indikator("iup", 7) == "IUP-07"
    assert id_indikator("ISV", 10) == "ISV-10"
    assert id_indikator("XXX", 1) is None
    assert id_indikator("ISV", None) is None


@pytest.mark.parametrize(
    "masukan,harapan",
    [
        ("Masuk, tetapi belum ada data", "MASUK_TAPI_BELUM_ADA_DATA"),
        ("Dobel ISV dan IUP", "DOBEL_ISV_IUP"),
        ("Tidak masuk RPJMD", "TIDAK_MASUK_RPJMD"),
        ("Masuk RPJMD", "MASUK_RPJMD"),
        ("", "TIDAK_MASUK_RPJMD"),
    ],
)
def test_enum_rpjmd(masukan, harapan):
    assert enum_rpjmd(masukan) == harapan


def test_kategori_diturunkan_dari_penomoran_menyambung():
    """Sheet lama menomori 1..10 sebagai ISV dan sisanya IUP."""
    assert kategori_dari_nomor(1, ISV_MAKS) == "ISV"
    assert kategori_dari_nomor(10, ISV_MAKS) == "ISV"
    assert kategori_dari_nomor(11, ISV_MAKS) == "IUP"
    assert kategori_dari_nomor(None, ISV_MAKS) is None


def test_nomor_iup_digeser_mundur_sebanyak_batas_isv():
    assert nomor_dalam_kategori(11, "IUP", ISV_MAKS) == 1
    assert nomor_dalam_kategori(4, "ISV", ISV_MAKS) == 4
    assert nomor_dalam_kategori(None, "IUP", ISV_MAKS) is None


def test_proxy_dengan_nama_dari_catatan():
    assert ekstrak_proxy("Ya", "Indikator proxy: TPT usia muda") == (1, "TPT usia muda")


def test_proxy_dari_penanda_bernama():
    """Kolom penanda yang berisi nama dipakai sebagai nama proxy."""
    assert ekstrak_proxy("Angka Melek Huruf", None) == (1, "Angka Melek Huruf")


def test_penanda_ya_saja_bukan_nama_proxy():
    assert ekstrak_proxy("Ya", None) == (1, None)


@pytest.mark.parametrize("penanda", ["Tidak", "tidak ada", "-", None])
def test_bukan_proxy(penanda):
    assert ekstrak_proxy(penanda, None) == (0, None)


def test_pdf_label_dan_pencocokan_nama():
    assert "Nama Indikator Rasio Gini" in normalize_labels("Nama Rasio Gini\nIndikator")
    assert (
        score_names(
            "Kontribusi PDRB Provinsi (%)",
            "Kontribusi Produk Domestik Regional Bruto Provinsi (%)",
        )
        >= 85
    )

"""Unit test perhitungan analitik dan aturan verifikasi — tanpa basis data."""

from __future__ import annotations

import pytest

from backend.app.services import analitik as svc
from backend.app.services import verifikasi as svc_verifikasi

# --- korelasi --------------------------------------------------------------


def test_korelasi_sempurna_positif():
    hasil = svc.korelasi({2021: 1, 2022: 2, 2023: 3, 2024: 4}, {2021: 2, 2022: 4, 2023: 6, 2024: 8})
    assert hasil.n == 4
    assert hasil.pearson == 1.0


def test_korelasi_sempurna_negatif():
    hasil = svc.korelasi({2021: 1, 2022: 2, 2023: 3, 2024: 4}, {2021: 8, 2022: 6, 2023: 4, 2024: 2})
    assert hasil.pearson == -1.0


def test_korelasi_seri_pendek_disembunyikan():
    """n < 4 lebih menyesatkan daripada berguna, jadi hasilnya ditahan."""
    hasil = svc.korelasi({2021: 1, 2022: 2, 2023: 3}, {2021: 2, 2022: 4, 2023: 6})
    assert hasil.n == 3
    assert hasil.pearson is None
    assert "n < 4" in hasil.peringatan


def test_korelasi_hanya_memakai_tahun_yang_dimiliki_keduanya():
    hasil = svc.korelasi(
        {2020: 9, 2021: 1, 2022: 2, 2023: 3, 2024: 4},
        {2021: 2, 2022: 4, 2023: 6, 2024: 8, 2025: 9},
    )
    assert hasil.n == 4
    assert [t["tahun"] for t in hasil.titik] == [2021, 2022, 2023, 2024]


def test_korelasi_seri_konstan_tidak_terdefinisi_bukan_nol():
    hasil = svc.korelasi({2021: 5, 2022: 5, 2023: 5, 2024: 5}, {2021: 1, 2022: 2, 2023: 3, 2024: 4})
    assert hasil.pearson is None
    assert hasil.n == 4


def test_korelasi_tanpa_tahun_bersama():
    hasil = svc.korelasi({2021: 1}, {2030: 1})
    assert hasil.n == 0
    assert hasil.titik == []


# --- selisih tahunan -------------------------------------------------------


def test_selisih_tahunan_arah_naik():
    hasil = svc.selisih_tahunan([(2021, 10.0), (2022, 12.0), (2023, 11.0)], "NAIK")
    assert hasil == [
        {"tahun": 2022, "selisih": 2.0, "membaik": True},
        {"tahun": 2023, "selisih": -1.0, "membaik": False},
    ]


def test_selisih_tahunan_arah_turun_membalik_penilaian():
    hasil = svc.selisih_tahunan([(2021, 10.0), (2022, 8.0)], "TURUN")
    assert hasil == [{"tahun": 2022, "selisih": -2.0, "membaik": True}]


def test_selisih_tahunan_seri_satu_titik():
    assert svc.selisih_tahunan([(2021, 10.0)], "NAIK") == []


def test_skor_perbaikan_selalu_makin_besar_makin_baik():
    assert svc.skor_perbaikan(3.0, "NAIK") == 3.0
    assert svc.skor_perbaikan(3.0, "TURUN") == -3.0


# --- gap dan laju ----------------------------------------------------------


def test_laju_historis():
    assert svc.laju_historis([(2021, 10.0), (2025, 18.0)]) == 2.0


def test_laju_historis_butuh_dua_titik_tahun_berbeda():
    assert svc.laju_historis([(2021, 10.0)]) is None
    assert svc.laju_historis([]) is None


def test_laju_dibutuhkan():
    assert svc.laju_dibutuhkan(10.0, 2025, 30.0, 2045) == 1.0


def test_laju_dibutuhkan_tanpa_target_atau_sudah_lewat():
    assert svc.laju_dibutuhkan(10.0, 2025, None, 2045) is None
    assert svc.laju_dibutuhkan(10.0, 2045, 30.0, 2045) is None


@pytest.mark.parametrize(
    "historis,dibutuhkan,arah,status",
    [
        (2.0, 1.0, "NAIK", "DI_JALUR"),
        (0.5, 1.0, "NAIK", "PERLU_AKSELERASI"),
        (-2.0, -1.0, "TURUN", "DI_JALUR"),
        (-0.5, -1.0, "TURUN", "PERLU_AKSELERASI"),
    ],
)
def test_status_jalur(historis, dibutuhkan, arah, status):
    assert svc.status_jalur(historis, dibutuhkan, arah, terverifikasi=True) == status


def test_status_jalur_tanpa_arah_terverifikasi():
    assert svc.status_jalur(2.0, 1.0, "NAIK", terverifikasi=False) == "BELUM_ADA_DATA"
    assert svc.status_jalur(None, 1.0, "NAIK", terverifikasi=True) == "BELUM_ADA_DATA"


# --- aturan verifikasi -----------------------------------------------------


def test_operator_hanya_boleh_mengusulkan_realisasi():
    penolakan = svc_verifikasi.periksa_pengusulan(
        peran="OPERATOR", jenis="target", wilayah_operator="6501", wilayah_diminta=None
    )
    assert penolakan is not None
    assert penolakan.kode == 403


def test_admin_boleh_mengusulkan_target():
    assert (
        svc_verifikasi.periksa_pengusulan(peran="ADMIN", jenis="target", wilayah_operator=None, wilayah_diminta="65")
        is None
    )


def test_jenis_asing_ditolak():
    penolakan = svc_verifikasi.periksa_pengusulan(
        peran="ADMIN", jenis="proyeksi", wilayah_operator=None, wilayah_diminta="65"
    )
    assert penolakan.kode == 422


def test_pengusulan_tanpa_wilayah_ditolak():
    penolakan = svc_verifikasi.periksa_pengusulan(
        peran="ADMIN", jenis="realisasi", wilayah_operator=None, wilayah_diminta=None
    )
    assert penolakan.kode == 422


def test_operator_terkunci_ke_wilayahnya():
    """Operator tidak dapat mengusulkan untuk wilayah lain meski memintanya."""
    assert svc_verifikasi.lingkup_wilayah(peran="OPERATOR", wilayah_operator="6501", wilayah_diminta="6502") == "6501"
    assert svc_verifikasi.lingkup_wilayah(peran="ADMIN", wilayah_operator=None, wilayah_diminta="6502") == "6502"


def _keputusan(**ubah):
    baku = {
        "keputusan": "DISETUJUI",
        "alasan": None,
        "peran_verifikator": "VERIFIKATOR",
        "wilayah_verifikator": "65",
        "pengusul_id": 2,
        "verifikator_id": 1,
    }
    return svc_verifikasi.periksa_keputusan(**{**baku, **ubah})


def test_keputusan_sah_lolos():
    assert _keputusan() is None


def test_keputusan_asing_ditolak():
    assert _keputusan(keputusan="MUNGKIN").kode == 422


def test_tidak_boleh_memverifikasi_usulan_sendiri():
    penolakan = _keputusan(pengusul_id=1, verifikator_id=1)
    assert penolakan.kode == 403
    assert "sendiri" in penolakan.pesan


def test_verifikator_harus_di_provinsi():
    penolakan = _keputusan(peran_verifikator="VERIFIKATOR", wilayah_verifikator="6501")
    assert penolakan.kode == 403


def test_verifikator_provinsi_boleh():
    assert _keputusan(peran_verifikator="VERIFIKATOR", wilayah_verifikator="65") is None


def test_admin_tidak_boleh_memutuskan_usulan():
    penolakan = _keputusan(peran_verifikator="ADMIN", wilayah_verifikator="65")
    assert penolakan and penolakan.kode == 403


def test_penolakan_wajib_beralasan():
    penolakan = _keputusan(keputusan="DITOLAK", alasan=None)
    assert penolakan.kode == 422
    assert _keputusan(keputusan="DITOLAK", alasan="Bukti tidak memadai") is None


def test_label_periode():
    assert svc_verifikasi.label_periode(2) == "Semester 2"
    assert svc_verifikasi.label_periode(3, "Triwulanan") == "Triwulan 3"
    assert svc_verifikasi.label_periode(None) is None
    assert svc_verifikasi.periode_sah(4) is True

"""Unit test aturan capaian — tanpa basis data, tanpa HTTP."""

from __future__ import annotations

import pytest

from backend.app.services import capaian as svc
from backend.app.services import nilai as svc_nilai

# --- capaian() -------------------------------------------------------------


def test_capaian_arah_naik():
    hasil = svc.capaian(80.0, 100.0, "NAIK", terverifikasi=True)
    assert hasil == (80.0, "PERLU_PERHATIAN")


def test_capaian_arah_turun_membalik_rasio():
    """Untuk indikator 'makin kecil makin baik', realisasi di bawah target = tercapai."""
    hasil = svc.capaian(4.0, 5.0, "TURUN", terverifikasi=True)
    assert hasil.persentase == 125.0
    assert hasil.status == "TERCAPAI"


@pytest.mark.parametrize(
    "persen,status",
    [
        (100, "TERCAPAI"),
        (150, "TERCAPAI"),
        (99.9, "MENDEKATI"),
        (90, "MENDEKATI"),
        (89.9, "PERLU_PERHATIAN"),
        (0, "PERLU_PERHATIAN"),
    ],
)
def test_ambang_status_capaian(persen: float, status: str):
    assert svc.status_capaian(persen) == status


@pytest.mark.parametrize(
    "realisasi,target,arah,verified",
    [
        (None, 100.0, "NAIK", True),
        (80.0, None, "NAIK", True),
        (80.0, 100.0, None, True),
        (80.0, 100.0, "NAIK", False),
    ],
)
def test_capaian_tanpa_bahan_lengkap_bukan_nol(realisasi, target, arah, verified):
    """Data tidak lengkap harus menghasilkan BELUM_ADA_DATA, bukan 0%."""
    hasil = svc.capaian(realisasi, target, arah, terverifikasi=verified)
    assert hasil == (None, "BELUM_ADA_DATA")


def test_capaian_arah_belum_diverifikasi_tidak_dihitung():
    """Menebak arah baik bisa membalik makna angka di dasbor."""
    assert svc.capaian(80.0, 100.0, "NAIK", terverifikasi=False).persentase is None


def test_capaian_pembagi_nol_tidak_meledak():
    assert svc.capaian(80.0, 0.0, "NAIK", terverifikasi=True) == (None, "BELUM_ADA_DATA")
    assert svc.capaian(0.0, 5.0, "TURUN", terverifikasi=True) == (None, "BELUM_ADA_DATA")


# --- progres_menuju() ------------------------------------------------------


def test_progres_setengah_jalan():
    assert svc.progres_menuju(50.0, 0.0, 100.0) == 50.0


def test_progres_dijepit_ke_atas_saat_melewati_target():
    assert svc.progres_menuju(150.0, 0.0, 100.0) == 100


def test_progres_dijepit_ke_bawah_saat_menjauh_dari_baseline():
    assert svc.progres_menuju(-20.0, 0.0, 100.0) == 0


def test_progres_baseline_sama_dengan_target():
    assert svc.progres_menuju(10.0, 10.0, 10.0) == 100
    assert svc.progres_menuju(11.0, 10.0, 10.0) is None


def test_progres_arah_turun():
    """Baseline 10 menuju target 5; realisasi 7,5 berarti separuh jalan."""
    assert svc.progres_menuju(7.5, 10.0, 5.0) == 50.0


def test_progres_tanpa_bahan():
    assert svc.progres_menuju(None, 0.0, 100.0) is None
    assert svc.progres_menuju(1.0, None, 100.0) is None
    assert svc.progres_menuju(1.0, 0.0, None) is None


# --- helper lain -----------------------------------------------------------


def test_arah_target_disimpulkan_dari_posisi_target():
    assert svc.arah_target(10.0, 20.0) == "NAIK"
    assert svc.arah_target(20.0, 10.0) == "TURUN"
    assert svc.arah_target(None, 10.0) is None


def test_membaik_mengikuti_arah():
    assert svc.membaik(11.0, 10.0, "NAIK") is True
    assert svc.membaik(9.0, 10.0, "NAIK") is False
    assert svc.membaik(9.0, 10.0, "TURUN") is True
    assert svc.membaik(9.0, 10.0, None) is None


def test_kebutuhan_per_tahun():
    assert svc.kebutuhan_per_tahun(20.0, 2025, 2045) == 1.0
    assert svc.kebutuhan_per_tahun(20.0, 2045, 2045) is None
    assert svc.kebutuhan_per_tahun(None, 2025, 2045) is None


# --- kalimat insight -------------------------------------------------------


def _kalimat(**ubah):
    baku = {
        "nama_indikator": "PDRB per Kapita",
        "nama_wilayah": "Kalimantan Utara",
        "tahun": 2025,
        "ada_nilai": True,
        "tahun_baseline": 2021,
        "progres_2029": 40.0,
        "progres_2045": 20.0,
        "target_2029": 327.0,
        "target_2045": 12.0,
        "sedang_membaik": True,
        "nilai_sekarang": 208.21,
        "nilai_baseline": 157.09,
        "satuan": "Juta Rupiah",
        "interpretasi": "Peningkatan PDRB per kapita menunjukkan penguatan kesejahteraan masyarakat. Kalimat kedua.",
        "riwayat": [(2021, 157.09), (2022, 192.59), (2023, 201.79), (2024, 198.68), (2025, 208.21)],
    }
    return svc.kalimat_insight(**{**baku, **ubah})


def test_insight_tanpa_nilai():
    assert "belum tersedia" in _kalimat(ada_nilai=False)


def test_insight_memakai_progres_2029_bukan_2045():
    """Kalimat harus mengikuti angka yang digambar cincin tracker."""
    kalimat = _kalimat()
    assert "PDRB per Kapita Kalimantan Utara pada 2025 tercatat 208,21 Juta Rupiah" in kalimat
    assert "target 2029" in kalimat
    assert "naik dari 157,09 Juta Rupiah pada 2021" in kalimat
    assert "Interpretasi indikator: Peningkatan PDRB per kapita" in kalimat
    assert "2045" not in kalimat


def test_insight_jatuh_ke_2045_bila_2029_tidak_ada():
    kalimat = _kalimat(progres_2029=None, target_2029=None)
    assert "Target 2029 belum tersedia" in kalimat
    assert "20.0% perjalanan" in kalimat


def test_insight_tanpa_target_sama_sekali():
    kalimat = _kalimat(target_2029=None, target_2045=None, progres_2029=None, progres_2045=None)
    assert kalimat == "Target 2029 dan 2045 belum tersedia sehingga progres belum dapat dihitung."


def test_insight_tren_menjauh():
    assert "masih cukup lebar" in _kalimat(sedang_membaik=False)


def test_insight_tren_tidak_dapat_dibandingkan():
    assert "target 2029" in _kalimat(sedang_membaik=None)


def test_insight_menyebut_tahun_yang_sempat_tertahan():
    assert "meski sempat tertahan pada 2024" in _kalimat()


# --- penafsiran nilai ------------------------------------------------------


def test_angka_terakhir_memakai_nilai_numerik():
    assert svc_nilai.angka_terakhir(3.85, "abaikan") == 3.85


def test_angka_terakhir_mengambil_angka_paling_belakang():
    """Teks '7,1; 7,4' adalah rilis per periode; yang mutakhir ada di belakang."""
    assert svc_nilai.angka_terakhir(None, "7,1; 7,4") == 7.4


def test_angka_terakhir_koma_desimal():
    assert svc_nilai.angka_terakhir(None, "3,85") == 3.85


def test_angka_terakhir_negatif():
    assert svc_nilai.angka_terakhir(None, "turun -2,5 persen") == -2.5


def test_angka_terakhir_tanpa_angka():
    assert svc_nilai.angka_terakhir(None, "belum tersedia") is None
    assert svc_nilai.angka_terakhir(None, None) is None
    assert svc_nilai.angka_terakhir(None, "") is None


def test_pertumbuhan():
    assert svc_nilai.pertumbuhan(110.0, 100.0) == 10.0
    assert svc_nilai.pertumbuhan(90.0, 100.0) == -10.0


def test_pertumbuhan_dari_nol_tidak_terdefinisi():
    assert svc_nilai.pertumbuhan(10.0, 0) is None
    assert svc_nilai.pertumbuhan(10.0, None) is None
    assert svc_nilai.pertumbuhan(None, 10.0) is None


def test_pertumbuhan_dari_angka_negatif_memakai_nilai_mutlak():
    assert svc_nilai.pertumbuhan(-5.0, -10.0) == 50.0


def test_arah_perubahan():
    assert svc_nilai.arah_perubahan(2.0, 1.0) == "NAIK"
    assert svc_nilai.arah_perubahan(1.0, 2.0) == "TURUN"
    assert svc_nilai.arah_perubahan(1.0, 1.0) == "TETAP"
    assert svc_nilai.arah_perubahan(None, 1.0) == "TIDAK_ADA_DATA"

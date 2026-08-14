from src.etl.arah_baik import infer_direction


def test_indikator_naik():
    assert infer_direction("PDRB per Kapita (Rp Juta)")[0] == "NAIK"
    assert infer_direction("Indeks Kualitas Lingkungan Hidup")[0] == "NAIK"
    assert infer_direction("Indeks Modal Manusia")[0] == "NAIK"


def test_indikator_turun():
    assert infer_direction("Tingkat Kemiskinan (%)")[0] == "TURUN"
    assert infer_direction("Rasio Gini")[0] == "TURUN"
    assert infer_direction("Penurunan intensitas emisi GRK")[0] == "TURUN"

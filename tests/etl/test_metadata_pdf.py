"""Unit test pembacaan kartu metadata dari teks PDF (tanpa membuka PDF)."""

from __future__ import annotations

from src.etl.metadata_pdf import field_value, label_positions, parse_cards

CHUNK = (
    "Definisi Nilai tambah bruto per penduduk. "
    "Rumus Perhitungan PDRB dibagi jumlah penduduk. "
    "Interpretasi Semakin tinggi semakin baik. "
    "Sumber Data BPS Provinsi. "
    "Frekuensi Tahunan."
)


def test_label_positions_menemukan_semua_label():
    positions = label_positions(CHUNK)
    assert set(positions) == {
        "Definisi",
        "Rumus Perhitungan",
        "Interpretasi",
        "Sumber Data",
        "Frekuensi",
    }


def test_field_value_berhenti_di_label_berikutnya():
    positions = label_positions(CHUNK)
    assert field_value(CHUNK, positions, "Definisi") == "Nilai tambah bruto per penduduk."
    assert field_value(CHUNK, positions, "Sumber Data") == "BPS Provinsi."
    assert field_value(CHUNK, positions, "Frekuensi") == "Tahunan."


def test_field_value_mengembalikan_none_untuk_label_absen():
    assert field_value("Definisi saja.", label_positions("Definisi saja."), "Frekuensi") is None


def test_parse_cards_memetakan_urutan_kolom_dengan_benar():
    """Urutan argumen Card harus mengikuti label, bukan kebetulan posisi."""
    (card,) = parse_cards([(12, "Nama Indikator PDRB per Kapita " + CHUNK)])
    assert card.name == "PDRB per Kapita"
    assert card.definition == "Nilai tambah bruto per penduduk."
    assert card.raw_formula == "PDRB dibagi jumlah penduduk."
    assert card.interpretation == "Semakin tinggi semakin baik."
    assert card.source == "BPS Provinsi."
    assert card.frequency == "Tahunan."
    assert card.page == 12

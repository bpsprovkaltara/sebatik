import unittest

from src.etl.common import clean_text, enum_rpjmd, indicator_id, parse_angka
from src.etl.metadata_pdf import normalize_labels, score_names
from src.etl.pipeline import extract_unit


class CommonTests(unittest.TestCase):
    def test_parse_angka_formats(self):
        self.assertEqual(parse_angka("227,10"), 227.10)
        self.assertEqual(parse_angka("0.251"), 0.251)
        self.assertEqual(parse_angka("1.612,75"), 1612.75)
        self.assertEqual(parse_angka(" 8,90 "), 8.9)
        self.assertIsNone(parse_angka("Tidak Tersedia"))
        self.assertEqual(parse_angka(" 1 612,75 "), 1612.75)
        self.assertEqual(parse_angka("1,612.75"), 1612.75)
        self.assertIsNone(parse_angka("n.a."))

    def test_clean_and_id(self):
        self.assertEqual(clean_text("Nama  \n indikator"), "Nama indikator")
        self.assertEqual(indicator_id("iup", 7), "IUP-07")

    def test_enum_rpjmd(self):
        self.assertEqual(enum_rpjmd("Masuk, tetapi belum ada data"), "MASUK_TAPI_BELUM_ADA_DATA")
        self.assertEqual(enum_rpjmd("Dobel ISV dan IUP"), "DOBEL_ISV_IUP")

    def test_extract_unit(self):
        self.assertEqual(extract_unit("PDRB per Kapita (Rp Juta)"), "Rp Juta")
        self.assertEqual(extract_unit("Indeks Modal Manusia"), "indeks")

    def test_pdf_label_and_fuzzy_name(self):
        self.assertIn("Nama Indikator Rasio Gini", normalize_labels("Nama Rasio Gini\nIndikator"))
        self.assertGreaterEqual(
            score_names("Kontribusi PDRB Provinsi (%)", "Kontribusi Produk Domestik Regional Bruto Provinsi (%)"), 85
        )


if __name__ == "__main__":
    unittest.main()

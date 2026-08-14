# Laporan Tahap 6 - Analitik

- Selisih YoY dan peringkat memperhitungkan arah NAIK/TURUN.
- Gap 2029/2045, required run-rate, dan laju historis tersedia dengan disclaimer linear.
- Endpoint multi-seri membatasi empat indikator.
- Pearson disembunyikan jika `n < 4` dan selalu disertai peringatan non-kausalitas.
- Snapshot awal berisi 86 indikator; riwayat berikutnya tumbuh setiap ETL/unggah disetujui.

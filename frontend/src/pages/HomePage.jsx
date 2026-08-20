import { RUTE, ke } from "../lib/rute";
import { WaveDivider } from "../Brand";
import * as endpoints from "../api/endpoints";
import { EmptyState, Panel, Reveal, SECTION_REVEAL, SectionHead } from "../ui";
import { AlertTriangle, Database, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { HomeDoors } from "../components/home/HomeDoors";
import { HomeHero } from "../components/home/HomeHero";
import { MacroCards } from "../components/home/MacroCards";
import { AvailabilityTracker } from "../components/home/AvailabilityTracker";
import { YearPicker } from "../components/home/YearPicker";
import { SiteFooter } from "../components/layout/SiteFooter";
import { Topbar } from "../components/layout/Topbar";
import { usePageTitle } from "../hooks/usePageTitle";
import { hasNumber, valueLabel, valueParts } from "../lib/format";

export default function HomePage() {
  const [year, setYear] = useState(""),
    [data, setData] = useState(null),
    [error, setError] = useState("");
  /* Beranda memakai kerangkanya sendiri, bukan <Shell>, jadi judul tabnya
     dipasang di sini — tanpa ini ia mewarisi judul halaman sebelumnya. */
  usePageTitle("Beranda");

  useEffect(() => {
    endpoints
      .beranda({ tahun: year })
      .then((x) => {
        setData(x);
        if (!year) setYear(String(x.tahun));
      })
      .catch((e) => setError(e.message));
  }, [year]);

  const groups = (data?.sasaran_visi || []).reduce((acc, x) => {
    (acc[x.arah_pembangunan] ??= []).push(x);
    return acc;
  }, {});

  return (
    <div className="app home-app">
      <div className="shell">
        <Topbar active={RUTE.beranda} />
        <HomeHero />
        <main>
          {error && (
            <div className="error">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}

          <Panel
            delay={40}
            className="availability-tracker"
            title="Ketersediaan Data ISV–IUP Provinsi Kalimantan Utara"
            actions={<YearPicker data={data} year={year} onYearChange={setYear} />}
            observe={SECTION_REVEAL}
          >
            <AvailabilityTracker items={data?.ketersediaan_tahunan || []} year={year} />
          </Panel>

          <Reveal as="section" className="home-section macro-section" delay={60} observe={SECTION_REVEAL}>
            <SectionHead kicker={`Outlook ${data?.tahun || ""}`} title="Indikator Makro Kalimantan Utara" />
            <MacroCards items={data?.indikator_makro || []} loading={!data} />
          </Reveal>

          {/* Ketiga bagian di bawah ini memakai ambang `SECTION_REVEAL`: masing-
            masing baru muncul setelah benar-benar dimasuki pembaca, bukan saat
            tepi atasnya baru mengintip. Kepalanya pun seragam — kicker, judul
            tebal, tanpa kalimat penjelas — supaya turun halaman terasa sebagai
            satu irama yang sama. */}
          {/* Bagian Sasaran Visi duduk di atas bidang biru yang diapit dua
            pembatas ombak. Bidangnya sewarna dengan lapis depan ombak, jadi
            pertemuan keduanya tidak menyisakan garis lurus — yang memisahkan
            bagian ini dari tetangganya adalah lengkungan ombak itu sendiri. */}
          <WaveDivider tone="band" />
          <div className="wave-band">
            <Reveal as="section" className="home-section" delay={60} observe={SECTION_REVEAL}>
              <SectionHead kicker="Sasaran visi" title="Capaian Indikator Sasaran Visi (ISV) Indonesia Emas 2045" />
              <div className="vision-grid">
                {Object.entries(groups).map(([group, items], i) => (
                  <article className="vision-card" style={{ "--tone": `var(--series-${(i % 6) + 1})` }} key={group}>
                    <header>
                      <span>{String(i + 1).padStart(2, "0")}</span>
                      <div>
                        <h3>{group}</h3>
                        <small>{items.length} indikator</small>
                      </div>
                    </header>
                    <div className="vision-list">
                      {items.map((x) => {
                        const nilai = valueParts(x.nilai, x.nilai_teks, x.satuan);
                        /* Baris keterangan di bawah angka dirakit sebagai daftar, bukan
                           rangkaian kondisi bersarang. Hanya target tahun berjalan yang
                           ditampilkan di sini: target akhir 2045 hidup di tracker halaman
                           Capaian, tempat ia berdampingan dengan cincin progres yang
                           memberinya konteks. */
                        const catatan = [];
                        if (x.label_periode) catatan.push(x.label_periode);
                        if (hasNumber(x.target) || x.target_teks)
                          catatan.push(`Target ${x.tahun}: ${valueLabel(x.target, x.target_teks, x.satuan)}`);
                        return (
                          <div key={x.id_indikator}>
                            <i>{x.kode_indikator}</i>
                            <span>{x.nama_indikator}</span>
                            <strong className={hasNumber(x.nilai) ? undefined : "is-empty"}>
                              <span className="vision-value-number">{nilai.number}</span>
                              {nilai.unit && (
                                <span className={`vision-value-unit${nilai.unit === "%" ? " is-symbol" : ""}`}>
                                  {nilai.unit}
                                </span>
                              )}
                              {catatan.map((baris) => (
                                <small key={baris}>{baris}</small>
                              ))}
                            </strong>
                          </div>
                        );
                      })}
                    </div>
                  </article>
                ))}
              </div>
              {data && !Object.keys(groups).length && (
                <EmptyState icon={Target} title="Sasaran visi belum tersedia" desc="Data akan muncul setelah indikator sasaran visi diverifikasi." />
              )}
            </Reveal>
          </div>
          <WaveDivider flip tone="band" />

          <Panel
            delay={80}
            className="availability-section"
            kicker="Kerangka pembangunan"
            title="Indikator menurut kerangka pembangunan"
            desc="Telusuri indikator yang tercakup pada setiap lapisan kerangka pembangunan."
            observe={SECTION_REVEAL}
          >
            <div className="availability-grid">
              {(data?.ketersediaan_kelompok || []).map((x, i) => (
                <article className="availability-card" style={{ "--tone": `var(--series-${(i % 6) + 1})` }} key={x.kode}>
                  <div className="availability-card-head">
                    <span>
                      <b>{x.jumlah_kelompok}</b> kelompok
                    </span>
                  </div>
                  <h3>{x.label}</h3>
                  <div className="framework-indicator-list">
                    {x.kelompok.map(item=><a href={ke(`${RUTE.indikator}?indikator=${encodeURIComponent(item.id_indikator[0])}`)} key={item.nama}>
                      <span>{item.nama}<small>{item.jumlah_indikator} indikator</small></span>
                    </a>)}
                  </div>
                </article>
              ))}
            </div>
            {data && !data.ketersediaan_kelompok?.length && (
              <EmptyState
                icon={Database}
                title="Ketersediaan belum dapat dihitung"
                desc="Klasifikasi indikator atau data realisasi belum tersedia."
              />
            )}
          </Panel>

          <HomeDoors />
        </main>
      </div>
      <SiteFooter office />
    </div>
  );
}

/* ==========================================================================
   Peta Kalimantan Utara
   ========================================================================== */

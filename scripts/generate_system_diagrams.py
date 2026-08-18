import math
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "diagram-sistem"
OUT.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path(r"C:\Windows\Fonts")
REGULAR = FONT_DIR / "arial.ttf"
BOLD = FONT_DIR / "arialbd.ttf"

NAVY = "#12304A"
BLUE = "#2878B5"
LIGHT_BLUE = "#EAF4FB"
GREEN = "#23865E"
LIGHT_GREEN = "#EAF7F1"
ORANGE = "#D97706"
LIGHT_ORANGE = "#FFF4DF"
RED = "#B64040"
LIGHT_RED = "#FCECEC"
PURPLE = "#7357A5"
LIGHT_PURPLE = "#F2EEFA"
GRAY = "#5F6B76"
LIGHT_GRAY = "#F4F6F8"
BORDER = "#B8C2CC"
WHITE = "#FFFFFF"
BLACK = "#17212B"


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else REGULAR), size)


def centered(draw, box, text, size=26, bold=False, fill=BLACK, spacing=7):
    x1, y1, x2, y2 = box
    width_chars = max(8, int((x2 - x1) / (size * 0.55)))
    lines = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=width_chars) or [""])
    value = "\n".join(lines)
    fnt = font(size, bold)
    bbox = draw.multiline_textbbox((0, 0), value, font=fnt, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text(((x1+x2-tw)/2, (y1+y2-th)/2), value, font=fnt, fill=fill, spacing=spacing, align="center")


def box(draw, xy, text, fill=WHITE, outline=BORDER, size=25, bold=False, radius=18, width=3):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    centered(draw, xy, text, size=size, bold=bold)


def pill(draw, xy, text, fill=NAVY):
    draw.rounded_rectangle(xy, radius=35, fill=fill)
    centered(draw, xy, text, size=27, bold=True, fill=WHITE)


def diamond(draw, center, w, h, text, fill=LIGHT_ORANGE, outline=ORANGE, size=23):
    cx, cy = center
    pts = [(cx, cy-h/2), (cx+w/2, cy), (cx, cy+h/2), (cx-w/2, cy)]
    draw.polygon(pts, fill=fill, outline=outline)
    draw.line(pts + [pts[0]], fill=outline, width=3, joint="curve")
    centered(draw, (cx-w*.34, cy-h*.30, cx+w*.34, cy+h*.30), text, size=size, bold=True)


def arrow(draw, start, end, color=GRAY, width=4, label=None, dashed=False, label_offset=(0, -24)):
    x1, y1 = start; x2, y2 = end
    if dashed:
        length = math.hypot(x2-x1, y2-y1)
        if length:
            ux, uy = (x2-x1)/length, (y2-y1)/length
            step, dash = 20, 11
            for d in range(0, int(length), step):
                a = (x1+ux*d, y1+uy*d)
                b = (x1+ux*min(d+dash, length), y1+uy*min(d+dash, length))
                draw.line([a, b], fill=color, width=width)
    else:
        draw.line([start, end], fill=color, width=width)
    ang = math.atan2(y2-y1, x2-x1)
    ah = 16
    p1 = (x2-ah*math.cos(ang-math.pi/6), y2-ah*math.sin(ang-math.pi/6))
    p2 = (x2-ah*math.cos(ang+math.pi/6), y2-ah*math.sin(ang+math.pi/6))
    draw.polygon([end, p1, p2], fill=color)
    if label:
        mx, my = (x1+x2)/2 + label_offset[0], (y1+y2)/2 + label_offset[1]
        bb = draw.textbbox((0,0), label, font=font(20, True))
        pad = 7
        draw.rounded_rectangle((mx-(bb[2]-bb[0])/2-pad, my-(bb[3]-bb[1])/2-pad, mx+(bb[2]-bb[0])/2+pad, my+(bb[3]-bb[1])/2+pad), 7, fill=WHITE)
        draw.text((mx-(bb[2]-bb[0])/2, my-(bb[3]-bb[1])/2), label, font=font(20, True), fill=color)


def title(draw, width, main, sub):
    draw.text((80, 48), main, font=font(44, True), fill=NAVY)
    draw.text((80, 106), sub, font=font(24), fill=GRAY)
    draw.line((80, 150, width-80, 150), fill="#DCE3E8", width=3)


def process_diagram():
    W, H = 3600, 2250
    im = Image.new("RGB", (W, H), WHITE); d = ImageDraw.Draw(im)
    title(d, W, "PROSES BISNIS SISTEM SEBATIK", "Alur pemantauan, pengusulan, verifikasi, dan administrasi data indikator ISV–IUP")
    lanes = [
        ("PENGUNJUNG", LIGHT_BLUE, BLUE),
        ("OPERATOR WILAYAH", LIGHT_GREEN, GREEN),
        ("VERIFIKATOR", LIGHT_ORANGE, ORANGE),
        ("ADMIN", LIGHT_PURPLE, PURPLE),
    ]
    x0, gap, lane_w, top, bottom = 70, 24, 846, 185, 2160
    for i, (name, _bg, accent) in enumerate(lanes):
        x = x0+i*(lane_w+gap)
        d.rounded_rectangle((x, top, x+lane_w, bottom), 22, fill=WHITE, outline=BORDER, width=3)
        d.rounded_rectangle((x, top, x+lane_w, top+92), 22, fill=accent)
        d.rectangle((x, top+60, x+lane_w, top+92), fill=accent)
        centered(d, (x, top, x+lane_w, top+92), name, 30, True, WHITE)

    # Public lane
    x = x0; cx=x+lane_w/2
    pill(d,(cx-125,310,cx+125,380),"MULAI",BLUE)
    pub=[(440,"Buka aplikasi SEBATIK"),(600,"Lihat beranda, indikator,\ncapaian, insight, dan validitas"),(790,"Pilih wilayah, tahun,\nindikator, dan filter"),(980,"Sistem menampilkan hanya\ndata yang telah disetujui"),(1170,"Unduh CSV, XLSX, detail\nindikator, atau paket data")]
    prev=(cx,380)
    for y,t in pub:
        arrow(d,prev,(cx,y),BLUE); box(d,(x+105,y,x+lane_w-105,y+120),t,LIGHT_BLUE,BLUE,24); prev=(cx,y+120)
    pill(d,(cx-125,1395,cx+125,1465),"SELESAI",BLUE); arrow(d,prev,(cx,1395),BLUE)

    # Operator lane
    x=x0+(lane_w+gap); cx=x+lane_w/2
    ops=[(310,"Login dan ganti kata sandi awal"),(460,"Pilih indikator dan tahun"),(610,"Isi realisasi, sumber,\ndan catatan"),(780,"Unggah bukti dukung wajib"),(930,"Kirim usulan"),(1080,"Status MENUNGGU_VERIFIKASI")]
    prev=None
    for y,t in ops:
        if prev: arrow(d,prev,(cx,y),GREEN)
        box(d,(x+105,y,x+lane_w-105,y+105),t,LIGHT_GREEN,GREEN,23); prev=(cx,y+105)
    arrow(d,prev,(cx,1275),GREEN); diamond(d,(cx,1360),400,170,"KEPUTUSAN\nVERIFIKATOR",LIGHT_ORANGE,ORANGE,22)
    box(d,(x+80,1535,x+lane_w-80,1660),"DITOLAK\nLihat alasan dan ajukan koreksi baru",LIGHT_RED,RED,22,True)
    arrow(d,(cx-100,1430),(cx-100,1535),RED,label="DITOLAK",label_offset=(-75,-5))
    box(d,(x+80,1785,x+lane_w-80,1910),"DISETUJUI\nNilai wilayah menjadi data terverifikasi",LIGHT_GREEN,GREEN,22,True)
    arrow(d,(cx+100,1430),(cx+100,1785),GREEN,label="DISETUJUI",label_offset=(150,100))
    arrow(d,(x+80,1598),(x+25,1598),RED); d.line((x+25,1598,x+25,512,x+105,512),fill=RED,width=4); arrow(d,(x+25,512),(x+105,512),RED)

    # Verifier lane
    x=x0+2*(lane_w+gap); cx=x+lane_w/2
    ver=[(310,"Login"),(475,"Buka antrean usulan\nseluruh wilayah"),(665,"Periksa nilai, sumber,\ncatatan, dan bukti")]
    prev=None
    for y,t in ver:
        if prev: arrow(d,prev,(cx,y),ORANGE)
        box(d,(x+105,y,x+lane_w-105,y+110),t,LIGHT_ORANGE,ORANGE,24); prev=(cx,y+110)
    arrow(d,prev,(cx,900),ORANGE); diamond(d,(cx,990),390,180,"LAYAK\nDISETUJUI?",LIGHT_ORANGE,ORANGE,23)
    box(d,(x+65,1180,x+lane_w/2-25,1310),"TOLAK\nIsi alasan",LIGHT_RED,RED,23,True)
    box(d,(x+lane_w/2+25,1180,x+lane_w-65,1310),"SETUJUI\nUsulan",LIGHT_GREEN,GREEN,23,True)
    arrow(d,(cx-100,1065),(x+lane_w*.27,1180),RED,label="TIDAK",label_offset=(-40,-12))
    arrow(d,(cx+100,1065),(x+lane_w*.73,1180),GREEN,label="YA",label_offset=(40,-12))
    box(d,(x+105,1470,x+lane_w-105,1605),"Perbarui nilai wilayah\ndan catat jejak audit",LIGHT_BLUE,BLUE,24,True)
    arrow(d,(x+lane_w*.73,1310),(cx,1470),GREEN)
    # Status penolakan kembali terlihat pada panel keputusan Operator.

    # Admin lane
    x=x0+3*(lane_w+gap); cx=x+lane_w/2
    box(d,(x+105,310,x+lane_w-105,420),"Login",LIGHT_PURPLE,PURPLE,25)
    arrow(d,(cx,420),(cx,505),PURPLE); diamond(d,(cx,595),420,180,"PILIH FUNGSI\nADMINISTRASI",LIGHT_PURPLE,PURPLE,22)
    items=[
        (770,"Kelola akun, peran, wilayah,\nstatus, dan reset kata sandi"),
        (940,"Verifikasi usulan operator"),
        (1110,"Koreksi arah baik indikator"),
        (1280,"Unggah Excel massal"),
        (1450,"Validasi dan jalankan ETL\npada database staging"),
        (1620,"Tinjau pratinjau perubahan"),
    ]
    prev=(cx,685)
    for y,t in items:
        arrow(d,prev,(cx,y),PURPLE); box(d,(x+80,y,x+lane_w-80,y+115),t,LIGHT_PURPLE,PURPLE,22); prev=(cx,y+115)
    arrow(d,prev,(cx,1830),PURPLE); diamond(d,(cx,1915),390,165,"SETUJUI\nPERUBAHAN?",LIGHT_ORANGE,ORANGE,22)
    box(d,(x+55,2070,x+lane_w/2-20,2140),"TIDAK · Produksi tetap",LIGHT_RED,RED,19,True)
    box(d,(x+lane_w/2+20,2070,x+lane_w-55,2140),"YA · Terapkan + audit",LIGHT_GREEN,GREEN,19,True)
    arrow(d,(cx-95,1980),(x+lane_w*.27,2070),RED)
    arrow(d,(cx+95,1980),(x+lane_w*.73,2070),GREEN)

    # Cross-lane information flow
    arrow(d,(x0+2*(lane_w+gap),1132),(x0+lane_w+gap+lane_w,1132),ORANGE,label="MASUK ANTREAN",dashed=True,label_offset=(0,-28))
    # Kotak biru pada lane Verifikator menandai pembaruan data publik.
    im.save(OUT/"01-proses-bisnis-sebatik.png", quality=96, dpi=(180,180))


def architecture_diagram():
    W,H=3000,1900
    im=Image.new("RGB",(W,H),WHITE); d=ImageDraw.Draw(im)
    title(d,W,"ARSITEKTUR SISTEM SEBATIK","Arsitektur aplikasi web, layanan API, proses data, penyimpanan, dan backup")
    # Zones
    zones=[(70,200,570,1750,"PENGGUNA",LIGHT_BLUE,BLUE),(630,200,2180,1750,"SERVER PRODUKSI · DOCKER",LIGHT_GREEN,GREEN),(2240,200,2930,1750,"DATA & OPERASIONAL",LIGHT_ORANGE,ORANGE)]
    for x1,y1,x2,y2,label,bg,accent in zones:
        d.rounded_rectangle((x1,y1,x2,y2),25,fill=bg,outline=accent,width=3)
        d.rounded_rectangle((x1,y1,x2,y1+82),25,fill=accent)
        d.rectangle((x1,y1+55,x2,y1+82),fill=accent)
        centered(d,(x1,y1,x2,y1+82),label,28,True,WHITE)
    # User
    box(d,(140,380,500,560),"Browser\nmobile",WHITE,BLUE,29,True)
    box(d,(140,700,500,880),"Browser\ndesktop / laptop",WHITE,BLUE,29,True)
    box(d,(140,1120,500,1300),"Admin · Operator\nVerifikator · Pengunjung",WHITE,BLUE,25,True)
    # Server components
    box(d,(740,340,2070,480),"CONTAINER SEBATIK · PORT 8000",GREEN,GREEN,31,True)
    box(d,(750,590,1330,790),"React SPA\nhasil build Vite\nHTML · CSS · JavaScript",WHITE,BLUE,25,True)
    box(d,(1470,590,2050,790),"FastAPI /api/v1\nREST · validasi · ekspor",WHITE,GREEN,25,True)
    box(d,(750,950,1330,1140),"JWT + Argon2\nKontrol akses per peran",WHITE,PURPLE,25,True)
    box(d,(1470,950,2050,1140),"SQLAlchemy\n+ SQL langsung",WHITE,GREEN,26,True)
    box(d,(750,1300,1330,1510),"ETL Excel / PDF\nopenpyxl · pdfplumber\ndatabase staging",WHITE,ORANGE,24,True)
    box(d,(1470,1300,2050,1510),"Penyimpanan berkas\narsip unggahan\n+ bukti dukung",WHITE,ORANGE,24,True)
    # Ops
    box(d,(2320,350,2850,540),"Sumber data\nExcel ISV–IUP · PDF\nmetadata · GeoJSON",WHITE,ORANGE,24,True)
    box(d,(2320,690,2850,890),"SQLite\nsebatik.db",WHITE,NAVY,32,True)
    box(d,(2320,1030,2850,1210),"Volume Docker\nsebatik_data",WHITE,GREEN,27,True)
    box(d,(2320,1370,2850,1540),"Backup harian\nretensi 30 salinan",WHITE,PURPLE,26,True)
    # Edges
    arrow(d,(500,470),(750,690),BLUE,label="HTTP / HTTPS",label_offset=(0,-32))
    arrow(d,(500,790),(750,690),BLUE)
    arrow(d,(500,1210),(750,1045),PURPLE,label="LOGIN & AKSES",label_offset=(0,-34))
    arrow(d,(1330,690),(1470,690),BLUE,label="fetch /api/v1",label_offset=(0,-30))
    arrow(d,(1760,790),(1040,950),PURPLE,label="AUTENTIKASI",label_offset=(0,-28))
    arrow(d,(1760,790),(1760,950),GREEN)
    arrow(d,(1760,1140),(2585,690),NAVY,label="BACA / TULIS",label_offset=(0,-30))
    arrow(d,(2585,540),(1040,1300),ORANGE,label="IMPOR",label_offset=(0,-30))
    arrow(d,(1330,1405),(2320,790),ORANGE,label="HASIL TERVERIFIKASI",label_offset=(0,-30))
    arrow(d,(1760,1140),(1760,1300),ORANGE)
    arrow(d,(2585,890),(2585,1030),GREEN,label="PERSISTEN",label_offset=(85,0))
    arrow(d,(2585,1210),(2585,1370),PURPLE,label="SALIN",label_offset=(60,0))
    arrow(d,(2050,1405),(2320,1120),ORANGE,label="SIMPAN",label_offset=(0,-25))
    # Dev strip
    d.rounded_rectangle((630,1780,2930,1870),20,fill=LIGHT_GRAY,outline=BORDER,width=2)
    centered(d,(650,1785,2910,1865),"PENGEMBANGAN: Vite dev server :5173  →  proxy /api  →  Uvicorn/FastAPI :8000",24,True,GRAY)
    im.save(OUT/"02-arsitektur-sistem-sebatik.png",quality=96,dpi=(180,180))


def database_diagram():
    W,H=3600,2600
    im=Image.new("RGB",(W,H),WHITE); d=ImageDraw.Draw(im)
    title(d,W,"DIAGRAM BASIS DATA SEBATIK","Entity relationship diagram — PK = primary key, FK = foreign key")
    groups=[
        (60,190,1160,2500,"MASTER & DATA UTAMA",LIGHT_BLUE,BLUE),
        (1200,190,2450,2500,"TATA KELOLA & WORKFLOW",LIGHT_GREEN,GREEN),
        (2490,190,3540,2500,"DATA PUBLIK / BERANDA",LIGHT_ORANGE,ORANGE),
    ]
    for x1,y1,x2,y2,label,bg,accent in groups:
        d.rounded_rectangle((x1,y1,x2,y2),24,fill=bg,outline=accent,width=3)
        d.rounded_rectangle((x1,y1,x2,y1+75),24,fill=accent); d.rectangle((x1,y1+50,x2,y1+75),fill=accent)
        centered(d,(x1,y1,x2,y1+75),label,27,True,WHITE)

    def table(x,y,w,h,name,rows,accent):
        d.rounded_rectangle((x,y,x+w,y+h),16,fill=WHITE,outline=accent,width=3)
        d.rounded_rectangle((x,y,x+w,y+62),16,fill=accent); d.rectangle((x,y+42,x+w,y+62),fill=accent)
        centered(d,(x,y,x+w,y+62),name,24,True,WHITE)
        yy=y+78
        for key,label in rows:
            color=RED if "PK" in key else PURPLE if "FK" in key else GRAY
            d.text((x+18,yy),key,font=font(18,True),fill=color)
            d.text((x+112,yy),label,font=font(19),fill=BLACK)
            yy+=31
        return (x,y,x+w,y+h)

    # Master/data utama
    indicator=table(105,310,1010,415,"indikator",[("PK","id_indikator"),("","kategori · nomor · nama_indikator"),("","kelompok · tim_pjk · satuan"),("","status_ketersediaan · status_metadata"),("","tahun_terakhir · is_proxy"),("","arah_baik · status_rpjmd")],BLUE)
    nilai=table(105,800,490,255,"nilai_indikator",[("PK/FK","id_indikator"),("PK","tahun · jenis"),("","nilai · sumber_sheet")],BLUE)
    meta=table(625,800,490,285,"metadata_indikator",[("PK/FK","id_indikator"),("","definisi · rumus"),("","interpretasi · sumber_data"),("","frekuensi · sumber_metadata")],BLUE)
    table(105,1160,490,240,"penugasan_pic",[("PK","id"),("FK","id_indikator"),("","jenis_pic · nama_pic")],BLUE)
    table(625,1160,490,240,"snapshot_ketersediaan",[("PK/FK","id_indikator"),("PK","tanggal_snapshot"),("","status")],BLUE)
    table(105,1510,1010,350,"log_perubahan",[("PK","id"),("FK","pengguna_id"),("FK","id_indikator"),("","field · nilai_lama · nilai_baru"),("","sumber_perubahan · referensi_id")],BLUE)

    # Governance
    wilayah=table(1245,310,540,275,"wilayah",[("PK","kode"),("FK","parent_kode (hierarki)"),("","nama · tingkat · aktif")],GREEN)
    user=table(1855,310,540,325,"pengguna",[("PK","id"),("FK","wilayah_kode"),("","username · password_hash"),("","peran · tim_pjk · aktif")],GREEN)
    usulan=table(1320,770,1000,450,"usulan_nilai",[("PK","id"),("FK","id_indikator · wilayah_kode"),("FK","pengusul_id · verifikator_id"),("","tahun · jenis · nilai · sumber"),("","status · alasan_verifikasi"),("","dibuat_pada · diverifikasi_pada")],GREEN)
    bukti=table(1245,1360,540,300,"bukti_dukung",[("PK","id"),("FK","usulan_id"),("","nama_file · path_file"),("","mime_type · ukuran · checksum")],GREEN)
    regional=table(1855,1360,540,350,"nilai_indikator_wilayah",[("PK/FK","id_indikator · wilayah_kode"),("PK","tahun · jenis"),("FK","usulan_id"),("","nilai · sumber"),("","diverifikasi_pada")],GREEN)
    table(1245,1830,540,320,"unggahan_excel",[("PK","id"),("FK","pengguna_id"),("","nama_file · path_arsip"),("","checksum · status"),("","ringkasan_diff")],GREEN)
    table(1855,1830,540,300,"log_aktivitas",[("PK","id"),("FK","pengguna_id"),("","aksi · objek_tipe · objek_id"),("","detail · waktu")],GREEN)

    # Public tables
    bi=table(2535,310,960,380,"beranda_indikator",[("PK","id_indikator"),("","kode · nama · kategori"),("","kelompok · satuan · opd_pengampu"),("","status_ketersediaan"),("","status_verifikasi · diverifikasi_pada")],ORANGE)
    bn=table(2535,850,960,315,"beranda_nilai",[("PK/FK","id_indikator"),("PK","tahun · jenis"),("","nilai · nilai_teks"),("","status_verifikasi")],ORANGE)
    bnw=table(2535,1340,960,390,"beranda_nilai_wilayah",[("PK/FK","id_indikator · wilayah_kode"),("PK","tahun · jenis"),("FK","usulan_id"),("","nilai · nilai_teks · sumber"),("","status_verifikasi")],ORANGE)
    filebox=table(2535,1910,960,285,"penyimpanan_berkas",[("","Bukan tabel / bukan BLOB"),("","Arsip unggahan Excel"),("","Bukti dukung PDF/JPG/PNG/XLSX"),("","Path dan checksum disimpan di DB")],ORANGE)

    # Relationship lines kept orthogonal and labeled
    def rel(a,b,label,color=GRAY,side_a="right",side_b="left",yoff=0):
        ax = a[2] if side_a=="right" else a[0]
        ay = (a[1]+a[3])/2 + yoff
        bx = b[0] if side_b=="left" else b[2]
        by = (b[1]+b[3])/2
        mid=(ax+bx)/2
        d.line((ax,ay,mid,ay,mid,by,bx,by),fill=color,width=4)
        arrow(d,(mid,by),(bx,by),color)
        bb=d.textbbox((0,0),label,font=font(17,True)); tw=bb[2]-bb[0]
        d.rounded_rectangle((mid-tw/2-7,ay-24,mid+tw/2+7,ay+7),7,fill=WHITE)
        d.text((mid-tw/2,ay-20),label,font=font(17,True),fill=color)
    rel(indicator,nilai,"1 : N",BLUE)
    rel(indicator,meta,"1 : 0..1",BLUE,yoff=35)
    rel(indicator,usulan,"1 : N",GREEN,yoff=70)
    rel(wilayah,user,"1 : N",GREEN)
    ux=(user[0]+user[2])/2; sx=(usulan[0]+usulan[2])/2
    d.line((ux,user[3],ux,710,sx,710,sx,usulan[1]),fill=GREEN,width=4)
    arrow(d,(sx,710),(sx,usulan[1]),GREEN)
    centered(d,(1810,665,2220,715),"pengusul / verifikator",17,True,GREEN)
    rel(usulan,bukti,"1 : N",GREEN,side_a="left",side_b="right",yoff=70)
    rel(usulan,regional,"1 : 0..1",GREEN,yoff=110)
    rel(bi,bn,"1 : N",ORANGE,side_a="left",side_b="right")
    rel(bi,bnw,"1 : N",ORANGE,side_a="left",side_b="right",yoff=50)
    rel(usulan,bnw,"terbit setelah disetujui",ORANGE,yoff=150)
    rel(bukti,filebox,"path + checksum",ORANGE,yoff=80)

    d.rounded_rectangle((105,2265,3290,2425),18,fill=WHITE,outline=BORDER,width=2)
    centered(d,(130,2280,3265,2410),"ALUR DATA: Operator membuat usulan + bukti  →  Verifikator menyetujui  →  nilai wilayah diperbarui  →  hanya data berstatus DISETUJUI yang tampil pada beranda",24,True,NAVY)
    im.save(OUT/"03-diagram-basis-data-sebatik.png",quality=96,dpi=(180,180))


if __name__ == "__main__":
    process_diagram()
    architecture_diagram()
    database_diagram()
    print(OUT)

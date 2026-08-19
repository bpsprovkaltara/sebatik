$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

python -m venv .venv-sebatik
$Python = Join-Path $ProjectRoot '.venv-sebatik\Scripts\python.exe'
& $Python -m pip install -r requirements.txt

Push-Location frontend
try {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        pnpm install
        pnpm build
    } elseif (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install
        npm run build
    } else {
        throw 'Node.js/npm belum tersedia. Pasang Node.js versi 20 atau lebih baru, lalu jalankan skrip ini kembali.'
    }
} finally {
    Pop-Location
}

# Skema dikelola Alembic, bukan lagi dibuat saat aplikasi mengimpor modul.
& $Python -m alembic -c backend/alembic.ini upgrade head

# Akun awal dibuat eksplisit. Sandinya acak dan hanya ditampilkan sekali di sini.
& $Python -m backend.app.cli seed --tampilkan-sandi

Write-Host ''
Write-Host 'Pemasangan selesai. Catat sandi di atas, lalu jalankan .\jalankan-sebatik.ps1' -ForegroundColor Green

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
python -m venv .venv-sebatik
& '.\.venv-sebatik\Scripts\python.exe' -m pip install -r requirements.txt
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
& '.\.venv-sebatik\Scripts\python.exe' -m src.etl.features
Write-Host 'Pemasangan selesai. Jalankan .\jalankan-sebatik.ps1' -ForegroundColor Green

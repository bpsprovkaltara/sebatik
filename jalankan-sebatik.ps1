$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $ProjectRoot '.venv-sebatik\Scripts\python.exe'
Set-Location $ProjectRoot
if (-not (Test-Path 'frontend\dist\index.html')) {
    throw 'Frontend belum dibangun. Jalankan pnpm install dan pnpm build di folder frontend.'
}
$FallbackPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$LocalPackages = Join-Path $ProjectRoot '.runtime-packages'
if ((Test-Path $FallbackPython) -and (Test-Path $LocalPackages)) {
    & $FallbackPython scripts\run_local_server.py
} elseif (Test-Path $PythonExe) {
    & $PythonExe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
} else {
    throw 'Runtime Python belum tersedia. Jalankan .\pasang-sebatik.ps1 terlebih dahulu.'
}

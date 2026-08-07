# Gera Clickr.exe via PyInstaller (Windows)
# Uso (na raiz do repo):
#   .\build_exe.ps1
# Saída: dist\Clickr.exe

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Instalando dependências (incl. pyinstaller)..."
python -m pip install -r requirements.txt
python -m pip install "pyinstaller>=6.0"

Write-Host "Regenerando ícone da marca (icon.png / icon.ico)..."
python .\scripts\generate_icon.py
if (-not (Test-Path "assets\icon.ico")) {
    Write-Error "Falha: assets\icon.ico não foi gerado."
    exit 1
}

Write-Host "Limpando builds anteriores..."
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

Write-Host "Empacotando Clickr..."
python -m PyInstaller --noconfirm Clickr.spec

$exe = Join-Path $PSScriptRoot "dist\Clickr.exe"
if (-not (Test-Path $exe)) {
    Write-Error "Build falhou: $exe não foi gerado."
    exit 1
}

Write-Host "OK: $exe"
Get-Item $exe | Format-List FullName, Length, LastWriteTime

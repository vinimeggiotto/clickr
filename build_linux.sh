#!/usr/bin/env bash
# Gera binário Clickr via PyInstaller (Linux)
# Uso (na raiz do repo):
#   ./build_linux.sh
# Saída: dist/Clickr
#
# Runtime típico: sessão X11, GTK/WebKit (pywebview), xprop para filtro de janela.

set -euo pipefail
cd "$(dirname "$0")"

echo "Instalando dependências (incl. pyinstaller)..."
python3 -m pip install -r requirements.txt
python3 -m pip install "pyinstaller>=6.0"

echo "Regenerando ícone da marca (icon.png / icon.ico)..."
python3 ./scripts/generate_icon.py
if [[ ! -f assets/icon.png ]]; then
  echo "Falha: assets/icon.png não foi gerado." >&2
  exit 1
fi

echo "Limpando builds anteriores..."
rm -rf dist/Clickr build/Clickr

echo "Empacotando Clickr (packaging/Clickr.linux.spec)..."
python3 -m PyInstaller --noconfirm packaging/Clickr.linux.spec

BIN="dist/Clickr"
if [[ ! -f "$BIN" ]]; then
  echo "Build falhou: $BIN não foi gerado." >&2
  exit 1
fi

chmod +x "$BIN"
echo "OK: $BIN"
ls -la "$BIN"

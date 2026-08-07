#!/usr/bin/env bash
# Gera Clickr.app via PyInstaller (macOS)
# Uso (na raiz do repo):
#   ./build_macos.sh
# Saída: dist/Clickr.app

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

# Gera icon.icns no macOS (sips + iconutil) quando disponível
if command -v sips >/dev/null 2>&1 && command -v iconutil >/dev/null 2>&1; then
  echo "Gerando assets/icon.icns..."
  ICONSET="build/Clickr.iconset"
  rm -rf "$ICONSET"
  mkdir -p "$ICONSET"
  for size in 16 32 64 128 256 512; do
    sips -z "$size" "$size" assets/icon.png --out "$ICONSET/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    if [[ "$double" -le 1024 ]]; then
      sips -z "$double" "$double" assets/icon.png --out "$ICONSET/icon_${size}x${size}@2x.png" >/dev/null
    fi
  done
  iconutil -c icns "$ICONSET" -o assets/icon.icns
  if [[ ! -f assets/icon.icns ]]; then
    echo "Falha: assets/icon.icns não foi gerado." >&2
    exit 1
  fi
else
  echo "Aviso: sips/iconutil indisponíveis; build seguirá sem icon.icns."
fi

echo "Limpando builds anteriores..."
rm -rf dist build/Clickr build/Clickr.app

echo "Empacotando Clickr (packaging/Clickr.macos.spec)..."
python3 -m PyInstaller --noconfirm packaging/Clickr.macos.spec

APP="dist/Clickr.app"
if [[ ! -d "$APP" ]]; then
  echo "Build falhou: $APP não foi gerado." >&2
  exit 1
fi

echo "OK: $APP"
ls -la "$APP"

#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-win10.txt

APP_NAME="bm-mouse-click_mac"

build_one() {
  local arch="$1"
  local out_name="${APP_NAME}_${arch}"

  pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "${out_name}" \
    --target-arch "${arch}" \
    --add-data "wav/switch.wav:wav" \
    main.py

  echo "Built: dist/${out_name}.app"
}

echo "Building macOS apps for: arm64, x86_64, universal2"
build_one "arm64"
build_one "x86_64"
build_one "universal2"

echo ""
echo "Done."
echo "Outputs:"
echo "  dist/${APP_NAME}_arm64.app"
echo "  dist/${APP_NAME}_x86_64.app"
echo "  dist/${APP_NAME}_universal2.app"

#!/usr/bin/env bash
# Builds a standalone Linux executable with PyInstaller
# Usage: ./build.sh

set -e

if [ -f ".venv/bin/pip" ]; then
    PIP=".venv/bin/pip"
    PYINSTALLER=".venv/bin/pyinstaller"
else
    PIP="pip"
    PYINSTALLER="pyinstaller"
fi

echo "==> Installing dependencies..."
$PIP install -q -r requirements.txt pyinstaller

# Generates icon.ico for the Windows build if missing
if [ ! -f "assets/icon.ico" ]; then
    echo "==> Generating assets/icon.ico..."
    python3 tools/generate_ico.py 2>/dev/null || true
fi

# Generates the --hidden-import flags for every module in sources/
HIDDEN=""
for f in sources/*.py; do
    mod=$(basename "$f" .py)
    [ "$mod" = "__init__" ] && continue
    HIDDEN="$HIDDEN --hidden-import sources.$mod"
done

echo "==> Building the Linux executable..."
$PYINSTALLER \
    --onefile \
    --windowed \
    --name "VentoyIsoUpdater" \
    --icon "assets/icon.png" \
    --add-data "data/distros.json:data" \
    --add-data "assets:assets" \
    --hidden-import customtkinter \
    --hidden-import PIL \
    --hidden-import PIL._tkinter_finder \
    --hidden-import packaging \
    --hidden-import packaging.version \
    --collect-all customtkinter \
    --distpath "dist/linux" \
    --workpath "build" \
    $HIDDEN \
    main.py

echo ""
echo "==> Binary generated: dist/linux/VentoyIsoUpdater"
echo ""
echo "    Available packages:"
echo "    ./package_deb.sh        -> dist/linux/*.deb"
echo "    ./package_rpm.sh        -> dist/linux/*.rpm"
echo "    ./package_appimage.sh   -> dist/linux/*.AppImage"
echo ""
echo "    To install directly:"
echo "    ./install.sh"

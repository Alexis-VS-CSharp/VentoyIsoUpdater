#!/usr/bin/env bash
# Build un exécutable standalone Linux avec PyInstaller
# Usage : ./build.sh

set -e

if [ -f ".venv/bin/pip" ]; then
    PIP=".venv/bin/pip"
    PYINSTALLER=".venv/bin/pyinstaller"
else
    PIP="pip"
    PYINSTALLER="pyinstaller"
fi

echo "==> Installation des dépendances..."
$PIP install -q -r requirements.txt pyinstaller

# Génère icon.ico pour le build Windows si absent
if [ ! -f "assets/icon.ico" ]; then
    echo "==> Génération de assets/icon.ico..."
    python3 tools/generate_ico.py 2>/dev/null || true
fi

# Génère les --hidden-import pour tous les modules sources/
HIDDEN=""
for f in sources/*.py; do
    mod=$(basename "$f" .py)
    [ "$mod" = "__init__" ] && continue
    HIDDEN="$HIDDEN --hidden-import sources.$mod"
done

echo "==> Build de l'exécutable Linux..."
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
echo "==> Binaire généré : dist/linux/VentoyIsoUpdater"
echo ""
echo "    Packages disponibles :"
echo "    ./package_deb.sh        → dist/linux/*.deb"
echo "    ./package_rpm.sh        → dist/linux/*.rpm"
echo "    ./package_appimage.sh   → dist/linux/*.AppImage"
echo ""
echo "    Pour installer directement :"
echo "    ./install.sh"

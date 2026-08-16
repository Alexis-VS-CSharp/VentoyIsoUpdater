#!/usr/bin/env bash
# Construit un AppImage — format portable universel Linux (zéro installation).
# Télécharge appimagetool dans tools/ si absent.
# Usage : ./package_appimage.sh

set -e

APP_NAME="VentoyIsoUpdater"
VERSION="${VERSION:-1.0.0}"   # surchargeable : VERSION=1.2.3 ./package_appimage.sh
BINARY="dist/linux/$APP_NAME"
APPIMAGE_TOOL="tools/appimagetool-x86_64.AppImage"
APPIMAGE_URL="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"

if [ ! -f "$BINARY" ]; then
    echo "ERREUR : $BINARY introuvable. Lancez ./build.sh d'abord."
    exit 1
fi

if [ ! -f "$APPIMAGE_TOOL" ]; then
    echo "==> Téléchargement de appimagetool dans tools/..."
    mkdir -p tools
    curl -L -o "$APPIMAGE_TOOL" "$APPIMAGE_URL"
    chmod +x "$APPIMAGE_TOOL"
fi

echo "==> Construction de l'AppImage..."

APPDIR="build/appimage/${APP_NAME}.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

cp "$BINARY" "$APPDIR/usr/bin/$APP_NAME"
chmod 755 "$APPDIR/usr/bin/$APP_NAME"

cp "assets/icon.png" "$APPDIR/$APP_NAME.png"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp "assets/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"

cat > "$APPDIR/$APP_NAME.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
GenericName=Gestionnaire de clé Ventoy
Comment=Gérez vos ISO Ventoy : vérification, téléchargement, thèmes
Exec=env BAMF_DESKTOP_FILE_HINT=${APPDIR}/$APP_NAME.desktop $APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;System;
Keywords=ventoy;usb;iso;linux;boot;
StartupWMClass=$APP_NAME
StartupNotify=true
EOF

cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/sh
exec "$APPDIR/usr/bin/VentoyIsoUpdater" "$@"
EOF
chmod +x "$APPDIR/AppRun"

OUTPUT="dist/linux/${APP_NAME}-${VERSION}-x86_64.AppImage"
ARCH=x86_64 "$APPIMAGE_TOOL" "$APPDIR" "$OUTPUT" 2>&1
chmod +x "$OUTPUT"

echo ""
echo "==> AppImage généré : $OUTPUT"
echo "    ./$OUTPUT"
echo ""
echo "    Intégration bureau complète (optionnel) :"
echo "    sudo apt install appimagelauncher"

#!/usr/bin/env bash
# Installe VentoyIsoUpdater pour l'utilisateur courant (pas besoin de sudo).
# Place le binaire, l'icône, et le .desktop pour intégration complète
# au gestionnaire de fichiers et à la taskbar.
#
# Usage : ./install.sh [chemin_binaire]
#   chemin_binaire : optionnel, par défaut dist/VentoyIsoUpdater

set -e

BINARY="${1:-dist/VentoyIsoUpdater}"
APP_NAME="VentoyIsoUpdater"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor"
DESKTOP_DIR="$HOME/.local/share/applications"

# ── Vérifications ─────────────────────────────────────────────────────────────

if [ ! -f "$BINARY" ]; then
    echo "ERREUR : binaire introuvable : $BINARY"
    echo "Lancez d'abord : ./build.sh"
    exit 1
fi

if [ ! -f "assets/icon.png" ]; then
    echo "ERREUR : assets/icon.png introuvable."
    exit 1
fi

# ── Installation du binaire ────────────────────────────────────────────────────

mkdir -p "$INSTALL_DIR"
cp "$BINARY" "$INSTALL_DIR/$APP_NAME"
chmod +x "$INSTALL_DIR/$APP_NAME"
echo "[1/4] Binaire installé : $INSTALL_DIR/$APP_NAME"

# ── Installation des icônes (plusieurs résolutions) ───────────────────────────

for size in 16 32 48 64 128 256; do
    dir="$ICON_DIR/${size}x${size}/apps"
    mkdir -p "$dir"
    if command -v convert &>/dev/null; then
        # ImageMagick disponible : redimensionne proprement
        convert "assets/icon.png" -resize "${size}x${size}" "$dir/$APP_NAME.png" 2>/dev/null \
            || cp "assets/icon.png" "$dir/$APP_NAME.png"
    else
        cp "assets/icon.png" "$dir/$APP_NAME.png"
    fi
done

# Icône scalable SVG (fallback = PNG 256 renommé)
mkdir -p "$ICON_DIR/scalable/apps"
cp "assets/icon.png" "$ICON_DIR/scalable/apps/$APP_NAME.png"
echo "[2/4] Icônes installées dans $ICON_DIR"

# ── Mise à jour du cache d'icônes ─────────────────────────────────────────────

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi
if command -v xdg-icon-resource &>/dev/null; then
    xdg-icon-resource install --novendor --size 256 "assets/icon.png" "$APP_NAME" 2>/dev/null || true
fi
echo "[3/4] Cache d'icônes mis à jour"

# ── Fichier .desktop ──────────────────────────────────────────────────────────

mkdir -p "$DESKTOP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VentoyIsoUpdater
GenericName=Gestionnaire de clé Ventoy
Comment=Gérez vos ISO Ventoy : vérification, téléchargement, thèmes
Exec=env BAMF_DESKTOP_FILE_HINT=$DESKTOP_FILE $INSTALL_DIR/$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;System;
Keywords=ventoy;usb;iso;linux;boot;
StartupWMClass=VentoyIsoUpdater
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

# Valide et enregistre le .desktop
if command -v desktop-file-validate &>/dev/null; then
    desktop-file-validate "$DESKTOP_FILE" 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v xdg-desktop-menu &>/dev/null; then
    xdg-desktop-menu install --novendor "$DESKTOP_FILE" 2>/dev/null || true
fi
echo "[4/4] Fichier .desktop installé : $DESKTOP_FILE"

# ── Résumé ────────────────────────────────────────────────────────────────────

echo ""
echo "✓ VentoyIsoUpdater installé avec succès !"
echo "  Binaire  : $INSTALL_DIR/$APP_NAME"
echo "  Icône    : $ICON_DIR/256x256/apps/$APP_NAME.png"
echo "  .desktop : $DESKTOP_FILE"
echo ""
echo "  Lancez l'app : VentoyIsoUpdater"
echo "  Ou depuis le menu application de votre bureau."
echo ""

# Si ~/.local/bin n'est pas dans le PATH, le signaler
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠  $HOME/.local/bin n'est pas dans votre PATH."
    echo "   Ajoutez cette ligne dans ~/.bashrc ou ~/.zshrc :"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
fi

#!/usr/bin/env bash
# Installs VentoyIsoUpdater for the current user (no sudo needed).
# Places the binary, icon, and .desktop file for full integration
# with the file manager and taskbar.
#
# Usage: ./install.sh [binary_path]
#   binary_path: optional, defaults to dist/VentoyIsoUpdater

set -e

BINARY="${1:-dist/VentoyIsoUpdater}"
APP_NAME="VentoyIsoUpdater"
INSTALL_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor"
DESKTOP_DIR="$HOME/.local/share/applications"

# ── Checks ─────────────────────────────────────────────────────────────

if [ ! -f "$BINARY" ]; then
    echo "ERROR: binary not found: $BINARY"
    echo "Run first: ./build.sh"
    exit 1
fi

if [ ! -f "assets/icon.png" ]; then
    echo "ERROR: assets/icon.png not found."
    exit 1
fi

# ── Binary installation ────────────────────────────────────────────────────

mkdir -p "$INSTALL_DIR"
cp "$BINARY" "$INSTALL_DIR/$APP_NAME"
chmod +x "$INSTALL_DIR/$APP_NAME"
echo "[1/4] Binary installed: $INSTALL_DIR/$APP_NAME"

# ── Icon installation (multiple resolutions) ───────────────────────────

for size in 16 32 48 64 128 256; do
    dir="$ICON_DIR/${size}x${size}/apps"
    mkdir -p "$dir"
    if command -v convert &>/dev/null; then
        # ImageMagick available: resizes cleanly
        convert "assets/icon.png" -resize "${size}x${size}" "$dir/$APP_NAME.png" 2>/dev/null \
            || cp "assets/icon.png" "$dir/$APP_NAME.png"
    else
        cp "assets/icon.png" "$dir/$APP_NAME.png"
    fi
done

# Scalable SVG icon (fallback = renamed PNG 256)
mkdir -p "$ICON_DIR/scalable/apps"
cp "assets/icon.png" "$ICON_DIR/scalable/apps/$APP_NAME.png"
echo "[2/4] Icons installed in $ICON_DIR"

# ── Icon cache update ─────────────────────────────────────────────

if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi
if command -v xdg-icon-resource &>/dev/null; then
    xdg-icon-resource install --novendor --size 256 "assets/icon.png" "$APP_NAME" 2>/dev/null || true
fi
echo "[3/4] Icon cache updated"

# ── .desktop file ──────────────────────────────────────────────────────────

mkdir -p "$DESKTOP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VentoyIsoUpdater
GenericName=Ventoy Drive Manager
Comment=Manage your Ventoy ISOs: update checks, downloads, themes
Exec=env BAMF_DESKTOP_FILE_HINT=$DESKTOP_FILE $INSTALL_DIR/$APP_NAME
Icon=$APP_NAME
Terminal=false
Categories=Utility;System;
Keywords=ventoy;usb;iso;linux;boot;
StartupWMClass=VentoyIsoUpdater
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

# Validates and registers the .desktop file
if command -v desktop-file-validate &>/dev/null; then
    desktop-file-validate "$DESKTOP_FILE" 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v xdg-desktop-menu &>/dev/null; then
    xdg-desktop-menu install --novendor "$DESKTOP_FILE" 2>/dev/null || true
fi
echo "[4/4] .desktop file installed: $DESKTOP_FILE"

# ── Summary ────────────────────────────────────────────────────────────────

echo ""
echo "✓ VentoyIsoUpdater installed successfully!"
echo "  Binary   : $INSTALL_DIR/$APP_NAME"
echo "  Icon     : $ICON_DIR/256x256/apps/$APP_NAME.png"
echo "  .desktop : $DESKTOP_FILE"
echo ""
echo "  Run the app: VentoyIsoUpdater"
echo "  Or from your desktop's application menu."
echo ""

# Warn if ~/.local/bin isn't in the PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠  $HOME/.local/bin is not in your PATH."
    echo "   Add this line to ~/.bashrc or ~/.zshrc:"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
fi

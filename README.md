🇬🇧 **English** · 🇫🇷 [Français](README.fr.md)

# VentoyIsoUpdater

A desktop GUI for managing Ventoy USB keys: checks for ISO updates, downloads with integrity verification, and manages the Ventoy GRUB2 theme.

## Features

- **Automatic detection** of mounted Ventoy drives (Linux and Windows)
- **Version checking** across 64 distribution checkers (108 registered variants: editions, architectures) — Ubuntu, Fedora, Debian, Arch, TrueNAS, Proxmox, etc.
- **ISO downloads** with a progress bar and **real checksum verification** (SHA256/SHA512/MD5/SHA1, whichever the upstream source publishes — not just a checkbox)
- **Version browser**: pick a specific version to download
- **Automatic `ventoy.json` updates**: new folders are registered as `menu_class` entries
- **GRUB2 theme management**:
  - `theme.txt` editor with automatic backup (`.bak`)
  - Theme image management (background, components)
  - Distro icon management (`icons/` folder)
  - Built-in logo repository (700+ Lutgaru icons)
  - Composited theme preview via PIL
- **Logos**: automatic download after each ISO, bulk sync
- **Persistent preferences**: download folder, last-used drive, window geometry
- **Bilingual interface**: French / English, switchable from the toolbar (applies on next restart)

## Requirements

- Python 3.11+
- **Linux only**: the system package `python3-tk` (Tk bindings aren't installable via pip — most desktop installs already have it; otherwise `sudo apt install python3-tk` / `sudo dnf install python3-tkinter` / `sudo pacman -S tk`)
- The Python dependencies listed in `requirements.txt`

## Installation (from source)

```bash
git clone https://github.com/celmax85/VentoyIsoUpdater
cd VentoyIsoUpdater
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build — a standalone executable per platform

**Important: PyInstaller does not cross-compile.** It produces an executable for the OS *it runs on* — you cannot generate a Windows `.exe` from Linux (except via Wine), or vice versa. Run the matching script on each target platform.

### Linux

```bash
./build.sh
# → dist/linux/VentoyIsoUpdater  (single executable, ~44 MB)
```

This script bundles Python, all dependencies (`--collect-all customtkinter`) and the 64 `sources/` checkers directly into the binary — at runtime it only depends on universal system libraries (`libc`, `libz`, `libpthread`), not on an external Tk/X11 install. It therefore runs as-is on most recent x86_64 distributions regardless of which one it was built on (the only real constraint is the `glibc` version: a binary built on a very recent distro may refuse to start on a much older one — standard practice for any Linux packaging, not a limitation of this project).

**The produced binary is unique and identical no matter which distribution format is chosen afterward** — `.deb`, `.rpm`, `.AppImage` are *not* separate builds, they're four different ways of packaging that same executable for each distro family's package manager:

| Script | Format | Target | Requires |
|---|---|---|---|
| `package_deb.sh` | `.deb` | Debian, Ubuntu, Mint, Pop!_OS… | `dpkg-deb` (present by default) |
| `package_rpm.sh` | `.rpm` | Fedora, RHEL, openSUSE, Rocky… | `rpm-build` (`sudo dnf install rpm-build`) |
| `package_appimage.sh` | `.AppImage` | **Universal** — nearly any distro, no install | Nothing (downloads `appimagetool` on first run) |
| `install.sh` | Direct copy | Any distro | Nothing — installs into `~/.local/bin` + menu entry, no root needed |

If you're unsure which format reaches the widest audience: the AppImage.

### Windows

Must be run **on Windows** (or via Wine from Linux):

```bat
build.bat
:: → dist\windows\VentoyIsoUpdater.exe
```

Then, pick one:
- `package_zip_win.bat` → a portable `.zip`, no install
- `package_installer_win.bat` → a classic `.exe` installer, requires [Inno Setup 6+](https://jrsoftware.org/isdl.php) installed on the build machine

### macOS

No build script provided yet — `python main.py` works (tkinter ships natively with Python on macOS), but no `.app`/`.dmg` is generated automatically.

### Automated builds and releases (GitHub Actions)

Two workflows run on GitHub-hosted runners (no manual build needed):

- **`.github/workflows/ci.yml`** — on every push/PR to `main`: tests (Python 3.11/3.12/3.13) + dependency audit (`pip-audit`).
- **`.github/workflows/release.yml`** — on every `vX.Y.Z` tag pushed: builds Linux (`.deb`/`.rpm`/`.AppImage`) on `ubuntu-latest` **and** Windows (portable `.zip` + `.exe` installer via Inno Setup) on `windows-latest` — two real machines of each OS, no cross-compilation — then automatically publishes a [GitHub Release](../../releases) with all packages attached.

To publish a new version:

```bash
git tag v1.2.3
git push origin v1.2.3
```

## Project structure

```
VentoyIsoUpdater/
├── main.py                  # Entry point
├── gui/
│   ├── app.py               # GUI (customtkinter)
│   └── i18n.py              # French/English translation lookup
├── core/
│   ├── ventoy_scanner.py    # Ventoy drive detection and ISO scanning
│   ├── version_checker.py   # Version-check orchestration
│   ├── downloader.py        # Downloads with progress + checksum
│   ├── ventoy_installer.py  # Installing Ventoy on a blank drive
│   ├── iso_manager.py       # ISO file management
│   ├── theme_manager.py     # GRUB2 theme management
│   └── preferences.py       # Persistent preferences
├── sources/                 # Per-distro version checkers (64 files)
│   ├── base.py               # BaseChecker ABC + VersionInfo
│   ├── _checksum.py          # Checksum-fetching helpers (GNU/BSD)
│   ├── _github.py            # GitHub releases helper
│   ├── ubuntu.py
│   ├── fedora.py
│   └── ...
├── data/
│   └── distros.json         # Distribution registry
├── assets/
│   ├── icon.png             # App icon
│   └── logos/               # Bundled logos (Pop!_OS, Proxmox, etc.)
├── requirements.txt
├── requirements-lock.txt    # Pinned versions, for reproducible builds
├── pyproject.toml
├── build.sh / build.bat
└── LICENSE
```

## Supported distributions

Ubuntu (+ Kubuntu/Xubuntu/Lubuntu/Ubuntu MATE/Budgie/Studio), Debian, LMDE, Fedora (Workstation/Server/KDE/Silverblue/Kinoite/Spins), Arch, Manjaro, EndeavourOS, CachyOS, Garuda (10 editions), Linux Mint, Pop!_OS, Zorin, elementary, deepin, openSUSE, Solus, Void Linux, Slackware, Gentoo, NixOS, MX Linux, antiX, Linux Lite, Peppermint, Q4OS, PCLinuxOS, Mageia, VanillaOS, SparkyLinux, Kali, Parrot, BlackArch, Qubes, Tails, Whonix, CentOS Stream, AlmaLinux, Rocky, Oracle Linux, TrueNAS SCALE, Univention UCS, Proxmox VE, pfSense, OPNsense, FreeBSD, OpenBSD, NetBSD, DragonFlyBSD, GhostBSD (3 editions), Bazzite, Nobara, Batocera, ChimeraOS, Lakka, Windows (official ISOs, manual verification), Hirens Boot CD, Clonezilla, GParted, SystemRescue, Memtest86+, Zentyal.

Nearly all ISOs downloaded through the app are checksum-verified (SHA256, SHA512, MD5, or SHA1, depending on what each distribution publishes) — see `SECURITY.md` for details on what is and isn't covered.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), in particular for adding a distribution.

## Security

Found a vulnerability? See [SECURITY.md](SECURITY.md) — please don't open a public issue.

## License

MIT — see [LICENSE](LICENSE)

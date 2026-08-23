🇬🇧 [English](README.md) · 🇫🇷 **Français**

# VentoyIsoUpdater

Interface graphique pour gérer vos clés USB Ventoy : vérification des mises à jour ISO, téléchargements avec empreinte d'intégrité, et gestion du thème GRUB2.

## Fonctionnalités

- **Détection automatique** des clés Ventoy montées (Linux et Windows)
- **Vérification des versions** pour 64 vérificateurs de distributions (123 variantes enregistrées : éditions, architectures) — Ubuntu, Fedora, Debian, Arch, TrueNAS, Proxmox, etc. x86_64 reste la cible prioritaire ; 13 distributions qui publient un vrai ISO ARM64 générique (pas une image spécifique à une carte SBC) ont une entrée séparée, clairement étiquetée « (ARM64) » — voir la liste des distributions supportées ci-dessous.
- **Téléchargement d'ISO** avec barre de progression et **vérification d'empreinte réelle** (SHA256/SHA512/MD5/SHA1 selon ce que publie chaque source — pas une simple case cochée)
- **Navigateur de versions** : choisissez une version spécifique à télécharger
- **Mise à jour automatique de ventoy.json** : les nouveaux dossiers sont enregistrés comme `menu_class`
- **Gestion du thème GRUB2** :
  - Éditeur de `theme.txt` avec sauvegarde automatique (`.bak`)
  - Gestion des images du thème (fond, composants)
  - Gestion des icônes de distros (dossier `icons/`)
  - Dépôt de logos intégré (700+ icônes Lutgaru)
  - Aperçu du thème composité avec PIL
- **Logos** : téléchargement automatique après chaque ISO, synchronisation en masse
- **Préférences persistantes** : dossier de téléchargement, dernière clé utilisée, géométrie de fenêtre
- **Interface bilingue** : français / anglais, changeable depuis la barre d'outils (appliqué au prochain redémarrage)

## Prérequis

- Python 3.11+
- **Linux uniquement** : le paquet système `python3-tk` (les bindings Tk ne sont pas installables via pip — la plupart des postes de bureau l'ont déjà, sinon `sudo apt install python3-tk` / `sudo dnf install python3-tkinter` / `sudo pacman -S tk`)
- Les dépendances Python listées dans `requirements.txt`

## Installation (depuis les sources)

```bash
git clone https://github.com/celmax85/VentoyIsoUpdater
cd VentoyIsoUpdater
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build — un exécutable autonome par plateforme

**Point important : PyInstaller ne fait pas de compilation croisée.** Il produit un exécutable pour l'OS *sur lequel il tourne* — impossible de générer un `.exe` Windows depuis Linux (sauf via Wine), ni l'inverse. Il faut donc lancer le bon script sur chaque plateforme cible.

### Linux

```bash
./build.sh
# → dist/linux/VentoyIsoUpdater  (exécutable unique, ~44 Mo)
```

Ce script embarque Python, toutes les dépendances (`--collect-all customtkinter`) et les 64 vérificateurs de `sources/` directement dans le binaire — à l'exécution, il ne dépend plus que de bibliothèques système universelles (`libc`, `libz`, `libpthread`), pas de Tk/X11 externe. Il tourne donc tel quel sur la plupart des distributions x86_64 récentes, quelle que soit celle utilisée pour le build (la seule contrainte réelle est la version de `glibc` : buildé sur une distribution trop récente, le binaire peut refuser de démarrer sur un système beaucoup plus ancien — pratique standard de tout packaging Linux, pas une limite de ce projet).

**Le binaire produit est unique et identique quel que soit le format de diffusion choisi ensuite** — `.deb`, `.rpm`, `.AppImage` ne sont *pas* des builds séparés, ce sont quatre façons différentes d'empaqueter ce même exécutable pour le gestionnaire de paquets de chaque famille de distribution :

| Script | Format | Cible | Nécessite |
|---|---|---|---|
| `package_deb.sh` | `.deb` | Debian, Ubuntu, Mint, Pop!_OS… | `dpkg-deb` (présent par défaut) |
| `package_rpm.sh` | `.rpm` | Fedora, RHEL, openSUSE, Rocky… | `rpm-build` (`sudo dnf install rpm-build`) |
| `package_appimage.sh` | `.AppImage` | **Universel** — quasi n'importe quelle distro, sans installation | Rien (télécharge `appimagetool` au premier lancement) |
| `install.sh` | Copie directe | N'importe quelle distro | Rien — installe dans `~/.local/bin` + entrée menu, sans droits root |

Si vous ne savez pas quel format choisir pour toucher le plus de monde : l'AppImage.

### Windows

Doit être lancé **sur Windows** (ou via Wine depuis Linux) :

```bat
build.bat
:: → dist\windows\VentoyIsoUpdater.exe
```

Puis, au choix :
- `package_zip_win.bat` → un `.zip` portable, sans installation
- `package_installer_win.bat` → un installateur classique (`.exe`), nécessite [Inno Setup 6+](https://jrsoftware.org/isdl.php) installé sur la machine qui build

### macOS

Pas de script de build fourni pour l'instant — `python main.py` fonctionne (tkinter est fourni nativement avec Python sur macOS), mais aucun `.app`/`.dmg` n'est généré automatiquement.

### Build et publication automatiques (GitHub Actions)

Deux workflows tournent sur les runners GitHub (pas besoin de builder à la main) :

- **`.github/workflows/ci.yml`** — à chaque push/PR sur `main` : tests (Python 3.11/3.12/3.13) + audit des dépendances (`pip-audit`).
- **`.github/workflows/release.yml`** — à chaque tag `vX.Y.Z` poussé : build Linux (`.deb`/`.rpm`/`.AppImage`) sur `ubuntu-latest` **et** Windows (`.zip` portable + installateur `.exe` via Inno Setup) sur `windows-latest` — deux vraies machines de chaque OS, pas de compilation croisée — puis publication automatique d'une [Release GitHub](../../releases) avec les quatre paquets attachés.

Pour publier une nouvelle version :

```bash
git tag v1.2.3
git push origin v1.2.3
```

## Structure du projet

```
VentoyIsoUpdater/
├── main.py                  # Point d'entrée
├── gui/
│   ├── app.py               # Interface graphique (customtkinter)
│   └── i18n.py              # Traductions français/anglais
├── core/
│   ├── ventoy_scanner.py    # Détection des clés Ventoy et scan des ISO
│   ├── version_checker.py   # Orchestration des vérifications de version
│   ├── downloader.py        # Téléchargements avec progression + empreinte
│   ├── ventoy_installer.py  # Installation de Ventoy sur une clé vierge
│   ├── iso_manager.py       # Gestion des fichiers ISO
│   ├── theme_manager.py     # Gestion du thème GRUB2
│   └── preferences.py       # Préférences persistantes
├── sources/                 # Vérificateurs de version par distro (64 fichiers)
│   ├── base.py               # BaseChecker ABC + VersionInfo
│   ├── _checksum.py          # Helpers de récupération d'empreinte (GNU/BSD)
│   ├── _github.py            # Helper GitHub releases
│   ├── ubuntu.py
│   ├── fedora.py
│   └── ...
├── data/
│   └── distros.json         # Base de données des distributions
├── assets/
│   ├── icon.png             # Icône de l'application
│   └── logos/               # Logos embarqués (Pop!OS, Proxmox, etc.)
├── requirements.txt
├── requirements-lock.txt    # Versions figées, pour builds reproductibles
├── pyproject.toml
├── build.sh / build.bat
└── LICENSE
```

## Distributions supportées

Ubuntu (+ Kubuntu/Xubuntu/Lubuntu/Ubuntu MATE/Budgie/Studio), Debian, LMDE, Fedora (Workstation/Server/KDE/Silverblue/Kinoite/Spins), Arch, Manjaro, EndeavourOS, CachyOS, Garuda (10 éditions), Linux Mint, Pop!_OS, Zorin, elementary, deepin, openSUSE, Solus, Void Linux, Slackware, Gentoo, NixOS, MX Linux, antiX, Linux Lite, Peppermint, Q4OS, PCLinuxOS, Mageia, VanillaOS, SparkyLinux, Kali, Parrot, BlackArch, Qubes, Tails, Whonix, CentOS Stream, AlmaLinux, Rocky, Oracle Linux, TrueNAS SCALE, Univention UCS, Proxmox VE, pfSense, OPNsense, FreeBSD, OpenBSD, NetBSD, DragonFlyBSD, GhostBSD (3 éditions), Bazzite, Nobara, Batocera, ChimeraOS, Lakka, Windows (ISOs officielles, vérification manuelle), Hirens Boot CD, Clonezilla, GParted, SystemRescue, Memtest86+, Zentyal.

La quasi-totalité des ISO téléchargées via l'app sont vérifiées par empreinte (SHA256, SHA512, MD5 ou SHA1 selon ce que publie chaque distribution) — voir `SECURITY.md` pour le détail de ce qui est et n'est pas couvert.

## Changelog

Voir [CHANGELOG.fr.md](CHANGELOG.fr.md) pour l'historique des versions.

## Contribuer

Voir [CONTRIBUTING.md](CONTRIBUTING.md), notamment pour ajouter une distribution.

## Sécurité

Une vulnérabilité à signaler ? Voir [SECURITY.md](SECURITY.md) — merci de ne pas ouvrir d'issue publique.

## Licence

MIT — voir [LICENSE](LICENSE)

"""
Détecte les clés Ventoy montées et liste les ISO présentes.
Compatible Linux et Windows.
"""

import os
import re
import sys
import json
import platform
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IsoEntry:
    filename: str
    path: str          # chemin absolu vers le fichier ISO
    folder: str        # dossier parent sur la clé (ex: 'linux', 'windows')
    size_bytes: int
    distro_id: Optional[str] = None    # id trouvé dans distros.json
    distro_name: Optional[str] = None
    local_version: Optional[str] = None
    logo_filename: Optional[str] = None


@dataclass
class VentoyDrive:
    mount_point: str
    label: str
    ventoy_version: Optional[str] = None
    iso_entries: list = field(default_factory=list)
    theme_dir: Optional[str] = None          # dossier racine du thème (ex: ventoy/M@N/)
    theme_icons_dir: Optional[str] = None    # sous-dossier icons/ du thème
    ventoy_json_path: Optional[str] = None   # chemin vers ventoy/ventoy.json


def find_ventoy_drives() -> list[VentoyDrive]:
    """Retourne la liste des clés Ventoy montées détectées."""
    drives = []
    system = platform.system()

    if system == "Linux":
        drives = _find_linux()
    elif system == "Windows":
        drives = _find_windows()

    return drives


def _is_ventoy_mount(path: str) -> bool:
    """Vérifie si le chemin est une clé Ventoy (présence du dossier ventoy/)."""
    ventoy_dir = os.path.join(path, "ventoy")
    return os.path.isdir(ventoy_dir)


def _get_ventoy_version(mount_point: str) -> Optional[str]:
    """Lit la version de Ventoy depuis ventoy/ventoy_release ou ventoy.json."""
    for candidate in [
        os.path.join(mount_point, "ventoy", "ventoy_release"),
        os.path.join(mount_point, "ventoy", "ventoy.json"),
    ]:
        if os.path.isfile(candidate):
            try:
                with open(candidate, encoding="utf-8", errors="replace") as f:
                    content = f.read()
                m = re.search(r"(\d+\.\d+\.\d+)", content)
                if m:
                    return m.group(1)
            except Exception:
                pass
    return None


def _find_theme_dir(mount_point: str) -> tuple[Optional[str], Optional[str]]:
    """
    Trouve le dossier racine du thème actif et son sous-dossier icons/.
    Retourne (theme_dir, icons_dir) — l'un ou les deux peuvent être None.

    Méthode 1 : lit ventoy/ventoy.json → theme.file → déduit le dossier parent.
    Méthode 2/3 : recherche récursive en fallback.
    """
    # Méthode 1 : lire ventoy.json pour trouver le chemin du thème
    ventoy_json = os.path.join(mount_point, "ventoy", "ventoy.json")
    if os.path.isfile(ventoy_json):
        try:
            with open(ventoy_json, encoding="utf-8") as f:
                data = json.load(f)
            theme_file = data.get("theme", {}).get("file", "")
            if theme_file:
                # theme_file ressemble à "/ventoy/M@N/theme.txt"
                theme_file_local = os.path.join(
                    mount_point,
                    theme_file.lstrip("/").replace("/", os.sep)
                )
                theme_dir = os.path.dirname(theme_file_local)
                if os.path.isdir(theme_dir):
                    icons_candidate = os.path.join(theme_dir, "icons")
                    return theme_dir, (icons_candidate if os.path.isdir(icons_candidate) else None)
        except Exception:
            pass

    # Méthode 2 : recherche récursive dans ventoy/themes/
    themes_root = os.path.join(mount_point, "ventoy", "themes")
    if os.path.isdir(themes_root):
        for dirpath, dirnames, _ in os.walk(themes_root):
            if "icons" in dirnames:
                return dirpath, os.path.join(dirpath, "icons")

    # Méthode 3 : cherche dans tout ventoy/
    ventoy_dir = os.path.join(mount_point, "ventoy")
    if os.path.isdir(ventoy_dir):
        for dirpath, dirnames, _ in os.walk(ventoy_dir):
            if "icons" in dirnames:
                return dirpath, os.path.join(dirpath, "icons")

    return None, None


def _get_drive_label_linux(mount_point: str) -> str:
    """Retourne le label du volume ou le nom du point de montage."""
    # Cherche via /dev/disk/by-label
    label_dir = "/dev/disk/by-label"
    if os.path.isdir(label_dir):
        for label in os.listdir(label_dir):
            link = os.path.realpath(os.path.join(label_dir, label))
            # vérifie si ce disque correspond au point de montage
            try:
                import subprocess
                result = subprocess.run(
                    ["findmnt", "-n", "-o", "SOURCE", mount_point],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    source = result.stdout.strip()
                    if os.path.realpath(os.path.join(label_dir, label)) == os.path.realpath(source):
                        return label.replace("\\x20", " ")
            except Exception:
                pass
    return os.path.basename(mount_point)


def _find_linux() -> list[VentoyDrive]:
    drives = []
    checked_paths = set()
    search_roots = []

    # Source principale : /proc/mounts liste exactement les vrais points de montage
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mp = parts[1]
                    if any(mp.startswith(b) for b in ["/media", "/run/media", "/mnt"]):
                        search_roots.append(mp)
    except Exception:
        pass

    # Fallback : scan limité à 2 niveaux de profondeur (jamais de rglob)
    # couvre /media/LABEL, /media/user/LABEL, /run/media/user/LABEL, /mnt/LABEL
    if not search_roots:
        for base in ["/media", "/run/media", "/mnt"]:
            if not os.path.isdir(base):
                continue
            base_dev = Path(base).stat().st_dev
            for lvl1 in Path(base).iterdir():
                if not lvl1.is_dir():
                    continue
                if lvl1.stat().st_dev != base_dev:
                    search_roots.append(str(lvl1))
                else:
                    for lvl2 in lvl1.iterdir():
                        if lvl2.is_dir() and lvl2.stat().st_dev != base_dev:
                            search_roots.append(str(lvl2))

    for mp in search_roots:
        mp = os.path.normpath(mp)
        if mp in checked_paths:
            continue
        checked_paths.add(mp)

        if _is_ventoy_mount(mp):
            label = _get_drive_label_linux(mp)
            version = _get_ventoy_version(mp)
            theme_dir, icons_dir = _find_theme_dir(mp)
            vjson = os.path.join(mp, "ventoy", "ventoy.json")
            drives.append(VentoyDrive(
                mount_point=mp,
                label=label,
                ventoy_version=version,
                theme_dir=theme_dir,
                theme_icons_dir=icons_dir,
                ventoy_json_path=vjson if os.path.isfile(vjson) else None,
            ))

    return drives


def _find_windows() -> list[VentoyDrive]:
    drives = []
    import string
    for letter in string.ascii_uppercase:
        mp = f"{letter}:\\"
        if os.path.isdir(mp) and _is_ventoy_mount(mp):
            try:
                import ctypes
                vol_label = ctypes.create_unicode_buffer(261)
                ctypes.windll.kernel32.GetVolumeInformationW(
                    mp, vol_label, 261, None, None, None, None, 0
                )
                label = vol_label.value or letter
            except Exception:
                label = letter
            version = _get_ventoy_version(mp)
            theme_dir, icons_dir = _find_theme_dir(mp)
            vjson = os.path.join(mp, "ventoy", "ventoy.json")
            drives.append(VentoyDrive(
                mount_point=mp,
                label=label,
                ventoy_version=version,
                theme_dir=theme_dir,
                theme_icons_dir=icons_dir,
                ventoy_json_path=vjson if os.path.isfile(vjson) else None,
            ))
    return drives


def scan_isos(drive: VentoyDrive, distros_db: dict) -> list[IsoEntry]:
    """
    Scanne la clé Ventoy et retourne la liste des ISO trouvées.
    Associe chaque ISO à une distro connue si possible.
    """
    entries = []
    mount = drive.mount_point

    for dirpath, dirnames, filenames in os.walk(mount):
        # Ignore le dossier ventoy/ (config interne)
        dirnames[:] = [
            d for d in dirnames
            if not (d.lower() == "ventoy" and dirpath == mount)
        ]

        for fname in filenames:
            if not fname.lower().endswith(".iso"):
                continue

            full_path = os.path.join(dirpath, fname)

            # Ignore les symlinks (sécurité : évite de suivre des liens malveillants)
            if os.path.islink(full_path):
                continue
            rel_folder = os.path.relpath(dirpath, mount)
            if rel_folder == ".":
                rel_folder = "/"

            try:
                size = os.path.getsize(full_path)
            except OSError:
                size = 0

            entry = IsoEntry(
                filename=fname,
                path=full_path,
                folder=rel_folder,
                size_bytes=size,
            )

            _match_distro(entry, distros_db)
            entries.append(entry)

    # Tri : par dossier puis par nom
    entries.sort(key=lambda e: (e.folder, e.filename))
    return entries


def _match_distro(entry: IsoEntry, distros_db: dict) -> None:
    """Tente d'associer un IsoEntry à une distro connue."""
    for distro in distros_db.get("distros", []):
        for pattern in distro.get("filename_patterns", []):
            if re.search(pattern, entry.filename, re.IGNORECASE):
                entry.distro_id = distro["id"]
                entry.distro_name = distro["name"]
                entry.logo_filename = distro.get("logo_filename")

                version_regex = distro.get("version_regex")
                if version_regex:
                    m = re.search(version_regex, entry.filename, re.IGNORECASE)
                    if m:
                        entry.local_version = m.group(1)
                return


def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en chaîne lisible."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def load_distros_db(json_path: Optional[str] = None) -> dict:
    """Charge la base de données des distros depuis distros.json."""
    if json_path is None:
        base = Path(__file__).parent.parent
        json_path = base / "data" / "distros.json"
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "distros" not in data:
            raise ValueError("Format distros.json invalide : clé 'distros' manquante")
        return data
    except (FileNotFoundError, PermissionError) as e:
        raise FileNotFoundError(f"Impossible d'ouvrir {json_path} : {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"distros.json corrompu : {e}") from e

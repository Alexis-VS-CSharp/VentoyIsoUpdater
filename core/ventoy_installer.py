"""
Utilitaires pour créer/installer Ventoy sur une clé USB vierge.
Compatible Linux et Windows.
"""

import os
import re
import json
import shutil
import hashlib
import platform
import subprocess
import tarfile
import zipfile
import tempfile
import requests
from typing import Optional, Callable


# ──────────────────────────────────────────────────────────────────────────────
#  Structures
# ──────────────────────────────────────────────────────────────────────────────

class UsbDrive:
    def __init__(self, device: str, name: str, size_bytes: int,
                 label: str = "", mountpoints: list = None):
        self.device = device          # ex: /dev/sdb  ou  E:\
        self.name = name              # nom court    ex: sdb
        self.size_bytes = size_bytes
        self.label = label
        self.mountpoints = mountpoints or []

    @property
    def display(self) -> str:
        from core.ventoy_scanner import format_size
        parts = [self.device]
        if self.label:
            parts.append(f'"{self.label}"')
        parts.append(format_size(self.size_bytes))
        if self.mountpoints:
            parts.append(f"({', '.join(m for m in self.mountpoints if m)})")
        return "  ".join(parts)


# ──────────────────────────────────────────────────────────────────────────────
#  Détection des clés USB disponibles
# ──────────────────────────────────────────────────────────────────────────────

def find_usb_drives(exclude_ventoy: bool = True) -> list[UsbDrive]:
    """Retourne les clés USB amovibles (non Ventoy si exclude_ventoy=True)."""
    system = platform.system()
    if system == "Linux":
        return _find_usb_linux(exclude_ventoy)
    elif system == "Windows":
        return _find_usb_windows(exclude_ventoy)
    return []


def _find_usb_linux(exclude_ventoy: bool) -> list[UsbDrive]:
    drives = []
    try:
        result = subprocess.run(
            ["lsblk", "-J", "-b", "-o", "NAME,SIZE,TYPE,HOTPLUG,LABEL,MOUNTPOINTS"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return drives
        data = json.loads(result.stdout)
        for dev in data.get("blockdevices", []):
            if dev.get("type") != "disk":
                continue
            if not dev.get("hotplug"):
                continue
            device = f"/dev/{dev['name']}"
            size = int(dev.get("size") or 0)
            label = dev.get("label") or ""
            # Collecte tous les points de montage des partitions
            mountpoints = []
            for child in dev.get("children", []):
                for mp in (child.get("mountpoints") or []):
                    if mp:
                        mountpoints.append(mp)
            if exclude_ventoy:
                from core.ventoy_scanner import _is_ventoy_mount
                if any(_is_ventoy_mount(mp) for mp in mountpoints):
                    continue
            drives.append(UsbDrive(
                device=device,
                name=dev["name"],
                size_bytes=size,
                label=label,
                mountpoints=mountpoints,
            ))
    except Exception:
        pass
    return drives


def _find_usb_windows(exclude_ventoy: bool) -> list[UsbDrive]:
    drives = []
    try:
        result = subprocess.run(
            ["wmic", "diskdrive", "where", "MediaType='Removable Media'",
             "get", "DeviceID,Size,MediaType,Model", "/format:csv"],
            capture_output=True, text=True, timeout=8
        )
        for line in result.stdout.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4 or not parts[1].startswith("\\\\.\\"):
                continue
            device = parts[1]
            size = int(parts[3]) if parts[3].isdigit() else 0
            drives.append(UsbDrive(device=device, name=device, size_bytes=size))
    except Exception:
        pass
    return drives


# ──────────────────────────────────────────────────────────────────────────────
#  Recherche de Ventoy déjà installé
# ──────────────────────────────────────────────────────────────────────────────

_LINUX_CANDIDATES = [
    "ventoy2disk.sh",
    "ventoy",
]
_LINUX_PATHS = [
    "/usr/share/ventoy/ventoy2disk.sh",
    "/opt/ventoy/ventoy2disk.sh",
    "/usr/local/share/ventoy/ventoy2disk.sh",
]


def find_ventoy_binary() -> Optional[str]:
    """
    Retourne le chemin de ventoy2disk.sh ou ventoy, ou None si non trouvé.

    Les emplacements d'installation standard (_LINUX_PATHS) sont vérifiés en
    priorité : ce sont des chemins absolus fixes, non influençables par
    l'environnement de l'utilisateur. La recherche dans $PATH via shutil.which
    n'intervient qu'en repli, car ce binaire est ensuite exécuté avec les
    droits root (pkexec/sudo) — un exécutable malveillant placé plus tôt dans
    $PATH ne doit pas pouvoir prendre la priorité sur une installation connue.
    """
    for path in _LINUX_PATHS:
        if os.path.isfile(path):
            return path
    for cmd in _LINUX_CANDIDATES:
        found = shutil.which(cmd)
        if found:
            return found
    return None


def find_ventoy_in_dir(directory: str) -> Optional[str]:
    """Cherche ventoy2disk.sh dans un répertoire extrait."""
    for fname in ["ventoy2disk.sh", "Ventoy2Disk.exe"]:
        candidate = os.path.join(directory, fname)
        if os.path.isfile(candidate):
            return candidate
    # Cherche récursivement un niveau plus profond
    for entry in os.scandir(directory):
        if entry.is_dir():
            candidate = os.path.join(entry.path, "ventoy2disk.sh")
            if os.path.isfile(candidate):
                return candidate
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  Téléchargement de Ventoy depuis GitHub
# ──────────────────────────────────────────────────────────────────────────────

def get_ventoy_latest_version() -> Optional[str]:
    """Récupère la dernière version de Ventoy depuis GitHub."""
    try:
        resp = requests.get(
            "https://api.github.com/repos/ventoy/Ventoy/releases/latest",
            timeout=12,
            headers={"Accept": "application/vnd.github+json"}
        )
        resp.raise_for_status()
        return resp.json().get("tag_name", "").lstrip("v")
    except Exception:
        return None


def _fetch_ventoy_checksum(version: str, archive_name: str) -> Optional[str]:
    """
    Récupère l'empreinte SHA256 officielle publiée par le projet Ventoy pour
    cette release (asset ``sha256.txt`` de la release GitHub) et retourne
    celle qui correspond à ``archive_name``. Retourne None si le fichier est
    injoignable ou ne contient pas d'entrée pour cette archive.
    """
    url = f"https://github.com/ventoy/Ventoy/releases/download/v{version}/sha256.txt"
    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
    except Exception:
        return None
    m = re.search(
        r"^([0-9a-fA-F]{64})\s+\*?" + re.escape(archive_name) + r"\s*$",
        resp.text, re.MULTILINE,
    )
    return m.group(1).lower() if m else None


def _sha256_file(path: str) -> str:
    """Calcule l'empreinte SHA256 d'un fichier local, par blocs."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_target(dest_dir: str, member_name: str) -> Optional[str]:
    """
    Résout le chemin de destination d'un membre d'archive et vérifie qu'il
    reste strictement contenu dans dest_dir. Protection contre les chemins
    de type ``../../`` ou absolus (zip slip / tar slip). Retourne le chemin
    résolu si sûr, None sinon.
    """
    dest_root = os.path.realpath(dest_dir)
    target = os.path.realpath(os.path.join(dest_root, member_name))
    if target == dest_root or target.startswith(dest_root + os.sep):
        return target
    return None


def _safe_extract_tar(archive_path: str, dest_dir: str) -> None:
    """Extrait une archive .tar.gz en rejetant tout membre dont le chemin
    sortirait de dest_dir, ainsi que les liens (symboliques ou durs)."""
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            if member.issym() or member.islnk():
                raise ValueError(f"Archive Ventoy refusée : lien suspect '{member.name}'")
            if _safe_member_target(dest_dir, member.name) is None:
                raise ValueError(f"Archive Ventoy refusée : chemin suspect '{member.name}'")
        try:
            # filter="data" (Python ≥ 3.12) : refuse en plus les métadonnées
            # dangereuses (device files, permissions setuid, etc.)
            tar.extractall(dest_dir, members=members, filter="data")
        except TypeError:
            # Python < 3.12 : le paramètre filter n'existe pas encore ;
            # la validation manuelle ci-dessus reste la protection effective.
            tar.extractall(dest_dir, members=members)


def _safe_extract_zip(archive_path: str, dest_dir: str) -> None:
    """Extrait une archive .zip en rejetant tout membre dont le chemin
    sortirait de dest_dir."""
    with zipfile.ZipFile(archive_path) as z:
        for name in z.namelist():
            if _safe_member_target(dest_dir, name) is None:
                raise ValueError(f"Archive Ventoy refusée : chemin suspect '{name}'")
        z.extractall(dest_dir)


def download_ventoy(
    version: str,
    dest_dir: str,
    on_progress: Optional[Callable] = None,
) -> Optional[str]:
    """
    Télécharge et extrait Ventoy dans dest_dir.

    L'archive est vérifiée par rapport à l'empreinte SHA256 officielle
    publiée par le projet Ventoy avant toute extraction, et les chemins de
    ses membres sont validés pour empêcher toute écriture hors de dest_dir.
    Si l'empreinte ne peut pas être récupérée ou ne correspond pas, le
    téléchargement est refusé (fail-closed : cette archive est ensuite
    exécutée avec les droits root via install_ventoy()).

    Retourne le chemin du dossier extrait, ou None en cas d'erreur.
    """
    system = platform.system()
    if system == "Linux":
        archive_name = f"ventoy-{version}-linux.tar.gz"
    else:
        archive_name = f"ventoy-{version}-windows.zip"

    url = (
        f"https://github.com/ventoy/Ventoy/releases/download/"
        f"v{version}/{archive_name}"
    )

    archive_path = os.path.join(dest_dir, archive_name)

    try:
        # timeout=(connect, read) : 30 s pour la connexion, 300 s max pour la lecture
        resp = requests.get(url, stream=True, timeout=(30, 300))
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0

        with open(archive_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if on_progress and total:
                        on_progress(done, total)

        # Vérification d'intégrité — obligatoire avant toute extraction/exécution
        expected = _fetch_ventoy_checksum(version, archive_name)
        if expected is None:
            os.remove(archive_path)
            return None
        if _sha256_file(archive_path).lower() != expected:
            os.remove(archive_path)
            return None

        # Extraction (chemins des membres validés, protège contre tar/zip slip)
        if archive_name.endswith(".tar.gz"):
            _safe_extract_tar(archive_path, dest_dir)
        elif archive_name.endswith(".zip"):
            _safe_extract_zip(archive_path, dest_dir)

        # Cherche le dossier extrait
        extracted = os.path.join(dest_dir, f"ventoy-{version}")
        if os.path.isdir(extracted):
            return extracted
        # Fallback : prend le premier dossier créé
        for entry in os.scandir(dest_dir):
            if entry.is_dir() and entry.name.startswith("ventoy"):
                return entry.path
        return dest_dir

    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  Installation de Ventoy
# ──────────────────────────────────────────────────────────────────────────────

def install_ventoy(
    device: str,
    ventoy_script: str,
    overwrite: bool = False,
    on_output: Optional[Callable[[str], None]] = None,
) -> tuple[bool, str]:
    """
    Installe Ventoy sur le périphérique device.
    Utilise pkexec si disponible (GUI sudo), sinon retourne une commande sudo.

    Retourne (succès: bool, message: str).
    """
    system = platform.system()
    flag = "-u" if overwrite else "-i"

    if system == "Linux":
        # Rend le script exécutable
        try:
            os.chmod(ventoy_script, 0o755)
        except Exception:
            pass

        # Choisit l'outil d'élévation
        if shutil.which("pkexec"):
            cmd = ["pkexec", ventoy_script, flag, device]
        elif shutil.which("sudo"):
            cmd = ["sudo", ventoy_script, flag, device]
        else:
            return False, (
                f"Impossible d'obtenir les droits root.\n"
                f"Exécutez manuellement :\n"
                f"  sudo {ventoy_script} {flag} {device}"
            )

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120
            )
            output = result.stdout + result.stderr
            if on_output:
                on_output(output)
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, "Délai d'attente dépassé."
        except Exception as e:
            return False, str(e)

    elif system == "Windows":
        # Sur Windows, Ventoy2Disk.exe doit être lancé avec élévation
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                return False, (
                    "Droits administrateur requis.\n"
                    "Relancez VentoyIsoUpdater en tant qu'administrateur."
                )
            result = subprocess.run(
                [ventoy_script, "-i", device],
                capture_output=True, text=True, timeout=120
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    return False, "Système non supporté."

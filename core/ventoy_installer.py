"""
Utilities for creating/installing Ventoy onto a blank USB drive.
Linux and Windows compatible.
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
        self.device = device          # e.g.: /dev/sdb  or  E:\
        self.name = name              # short name    e.g.: sdb
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
#  Detecting available USB drives
# ──────────────────────────────────────────────────────────────────────────────

def find_usb_drives(exclude_ventoy: bool = True) -> list[UsbDrive]:
    """Returns removable USB drives (non-Ventoy ones if exclude_ventoy=True)."""
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
            # Collects all mount points of the partitions
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
#  Finding an already-installed Ventoy
# ──────────────────────────────────────────────────────────────────────────────

_LINUX_CANDIDATES = [
    "Ventoy2Disk.sh",
    "ventoy2disk.sh",
    "ventoy",
]
_LINUX_PATHS = [
    "/usr/share/ventoy/Ventoy2Disk.sh",
    "/usr/share/ventoy/ventoy2disk.sh",
    "/opt/ventoy/Ventoy2Disk.sh",
    "/opt/ventoy/ventoy2disk.sh",
    "/usr/local/share/ventoy/Ventoy2Disk.sh",
    "/usr/local/share/ventoy/ventoy2disk.sh",
]


def find_ventoy_binary() -> Optional[str]:
    """
    Returns the path to Ventoy2Disk.sh or ventoy, or None if not found.

    The standard install locations (_LINUX_PATHS) are checked first: these
    are fixed absolute paths that the user's environment can't influence.
    Searching $PATH via shutil.which only happens as a fallback, since this
    binary is later executed with root privileges (pkexec/sudo) — a
    malicious executable placed earlier in $PATH must not be able to take
    priority over a known installation.
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
    """Looks for Ventoy2Disk.sh in an extracted directory."""
    # The official Ventoy Linux archive ships "Ventoy2Disk.sh" (mixed case);
    # the lowercase variant is also accepted in case a third-party package
    # renamed it — matching matters on case-sensitive filesystems (ext4, etc.)
    for fname in ["Ventoy2Disk.sh", "ventoy2disk.sh", "Ventoy2Disk.exe"]:
        candidate = os.path.join(directory, fname)
        if os.path.isfile(candidate):
            return candidate
    # Searches one level deeper, recursively
    for entry in os.scandir(directory):
        if entry.is_dir():
            for fname in ["Ventoy2Disk.sh", "ventoy2disk.sh"]:
                candidate = os.path.join(entry.path, fname)
                if os.path.isfile(candidate):
                    return candidate
    return None


_VENTOY_CACHE_DIR = os.path.join(
    os.path.expanduser("~"), ".local", "share", "ventoyisoupdater", "ventoy"
)


def get_ventoy_cache_dir() -> str:
    """
    Persistent folder for a downloaded Ventoy release, so it survives
    closing and reopening the "Create a Ventoy drive" wizard (it used to be
    a throwaway tempdir, silently forgotten — and re-downloaded — every
    time the wizard was reopened).
    """
    os.makedirs(_VENTOY_CACHE_DIR, exist_ok=True)
    return _VENTOY_CACHE_DIR


def find_cached_ventoy() -> Optional[str]:
    """Returns the install script from a previously downloaded release
    sitting in the persistent cache dir (most recently extracted first), or
    None if nothing has been downloaded yet."""
    if not os.path.isdir(_VENTOY_CACHE_DIR):
        return None
    subdirs = [
        os.path.join(_VENTOY_CACHE_DIR, name)
        for name in os.listdir(_VENTOY_CACHE_DIR)
        if os.path.isdir(os.path.join(_VENTOY_CACHE_DIR, name))
    ]
    for directory in sorted(subdirs, key=os.path.getmtime, reverse=True):
        script = find_ventoy_in_dir(directory)
        if script:
            return script
    return None


# ──────────────────────────────────────────────────────────────────────────────
#  Downloading Ventoy from GitHub
# ──────────────────────────────────────────────────────────────────────────────

def get_ventoy_latest_version() -> Optional[str]:
    """Fetches the latest Ventoy version from GitHub."""
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
    Fetches the official SHA256 checksum published by the Ventoy project for
    this release (the GitHub release's ``sha256.txt`` asset) and returns the
    one matching ``archive_name``. Returns None if the file is unreachable
    or has no entry for this archive.
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
    """Computes the SHA256 checksum of a local file, block by block."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_member_target(dest_dir: str, member_name: str) -> Optional[str]:
    """
    Resolves an archive member's destination path and checks that it stays
    strictly contained within dest_dir. Protects against ``../../`` or
    absolute paths (zip slip / tar slip). Returns the resolved path if
    safe, None otherwise.
    """
    dest_root = os.path.realpath(dest_dir)
    target = os.path.realpath(os.path.join(dest_root, member_name))
    if target == dest_root or target.startswith(dest_root + os.sep):
        return target
    return None


def _safe_extract_tar(archive_path: str, dest_dir: str) -> None:
    """Extracts a .tar.gz archive, rejecting any member whose path would
    escape dest_dir, as well as any link (symbolic or hard)."""
    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        for member in members:
            if member.issym() or member.islnk():
                raise ValueError(f"Ventoy archive rejected: suspicious link '{member.name}'")
            if _safe_member_target(dest_dir, member.name) is None:
                raise ValueError(f"Ventoy archive rejected: suspicious path '{member.name}'")
        try:
            # filter="data" (Python >= 3.12): also rejects dangerous
            # metadata (device files, setuid permissions, etc.)
            tar.extractall(dest_dir, members=members, filter="data")
        except TypeError:
            # Python < 3.12: the filter parameter doesn't exist yet;
            # the manual validation above remains the effective protection.
            tar.extractall(dest_dir, members=members)


def _safe_extract_zip(archive_path: str, dest_dir: str) -> None:
    """Extracts a .zip archive, rejecting any member whose path would
    escape dest_dir."""
    with zipfile.ZipFile(archive_path) as z:
        for name in z.namelist():
            if _safe_member_target(dest_dir, name) is None:
                raise ValueError(f"Ventoy archive rejected: suspicious path '{name}'")
        z.extractall(dest_dir)


def download_ventoy(
    version: str,
    dest_dir: str,
    on_progress: Optional[Callable] = None,
) -> Optional[str]:
    """
    Downloads and extracts Ventoy into dest_dir.

    The archive is checked against the official SHA256 checksum published
    by the Ventoy project before any extraction, and its members' paths
    are validated to prevent any write outside dest_dir. If the checksum
    can't be fetched or doesn't match, the download is rejected
    (fail-closed: this archive is later executed with root privileges via
    install_ventoy()).

    Returns the path of the extracted folder, or None on error.
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
        # timeout=(connect, read): 30s for the connection, 300s max for reading
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

        # Integrity check — mandatory before any extraction/execution
        expected = _fetch_ventoy_checksum(version, archive_name)
        if expected is None:
            os.remove(archive_path)
            return None
        if _sha256_file(archive_path).lower() != expected:
            os.remove(archive_path)
            return None

        # Extraction (member paths validated, protects against tar/zip slip)
        if archive_name.endswith(".tar.gz"):
            _safe_extract_tar(archive_path, dest_dir)
        elif archive_name.endswith(".zip"):
            _safe_extract_zip(archive_path, dest_dir)

        # dest_dir is now a persistent cache, not a throwaway tempdir —
        # don't leave the ~20MB archive behind on every download
        try:
            os.remove(archive_path)
        except OSError:
            pass

        # Looks for the extracted folder
        extracted = os.path.join(dest_dir, f"ventoy-{version}")
        if os.path.isdir(extracted):
            return extracted
        # Fallback: takes the first folder created
        for entry in os.scandir(dest_dir):
            if entry.is_dir() and entry.name.startswith("ventoy"):
                return entry.path
        return dest_dir

    except Exception:
        return None


# ──────────────────────────────────────────────────────────────────────────────
#  Installing Ventoy
# ──────────────────────────────────────────────────────────────────────────────

def install_ventoy(
    device: str,
    ventoy_script: str,
    overwrite: bool = False,
    on_output: Optional[Callable[[str], None]] = None,
) -> tuple[bool, str]:
    """
    Installs Ventoy onto the device.
    Uses pkexec if available (GUI sudo), otherwise returns a sudo command.

    Returns (success: bool, message: str).
    """
    system = platform.system()
    flag = "-u" if overwrite else "-i"

    if system == "Linux":
        # Makes the script executable
        try:
            os.chmod(ventoy_script, 0o755)
        except Exception:
            pass

        # Picks the elevation tool
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
            # Ventoy2Disk.sh itself has no non-interactive flag: it always
            # asks "Continue? (y/n)" on stdin before wiping the disk (twice,
            # for a plain -i install). Without an answer piped in, the read
            # either blocks until this call times out, or — if stdin is
            # already closed (e.g. launched from a desktop file) — hits EOF
            # immediately, silently reads it as "no" and exits 0, which we'd
            # then wrongly report as a successful install that touched
            # nothing on disk. The confirmation is already shown to the user
            # beforehand in _confirm_install(), so answering "y" here is safe.
            result = subprocess.run(
                cmd, input="y\ny\n", capture_output=True, text=True, timeout=180
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
        # On Windows, Ventoy2Disk.exe must be launched with elevation
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

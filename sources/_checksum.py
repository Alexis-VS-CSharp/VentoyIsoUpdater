"""
Helpers génériques pour récupérer une empreinte SHA256 publiée par une source
amont, à partir d'un fichier de sommes de contrôle en texte brut.
Utilisé par les vérificateurs qui exposent un vrai `checksum` (par opposition
à `checksum_type` seul, qui ne déclenche aucune vérification — voir
core/downloader.py::download_file).

Best effort : toute erreur réseau/format retourne None plutôt que de lever,
pour ne jamais faire échouer la vérification de version à cause d'un
problème sur le fichier de sommes de contrôle.
"""

import re
import requests
from typing import Optional
from core.logger import logger


def fetch_gnu_hashsum(url: str, filename: str, hex_len: int = 64, timeout: int = 10) -> Optional[str]:
    """
    Télécharge un fichier de sommes de contrôle au format GNU coreutils
    (ex: 'SHA256SUMS', 'sha512sum.txt', '<fichier>.sha512sum') et retourne
    l'empreinte associée à `filename`, ou None si absente/injoignable.
    Formats acceptés : "<hash>  <filename>" et "<hash> *<filename>".
    `hex_len` : longueur de l'empreinte en hexadécimal (64 = sha256,
    128 = sha512, 32 = md5, 40 = sha1).
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: échec ignoré : %s", __name__, _exc)
        return None
    pattern = re.compile(
        r"^([0-9a-fA-F]{" + str(hex_len) + r"})\s+\*?(?:\./)?" + re.escape(filename) + r"\s*$",
        re.MULTILINE,
    )
    m = pattern.search(resp.text)
    return m.group(1).lower() if m else None


def fetch_sha256sums(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Raccourci fetch_gnu_hashsum(hex_len=64) — voir sa docstring."""
    return fetch_gnu_hashsum(url, filename, hex_len=64, timeout=timeout)


def fetch_sha512sums(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Raccourci fetch_gnu_hashsum(hex_len=128) — voir sa docstring."""
    return fetch_gnu_hashsum(url, filename, hex_len=128, timeout=timeout)


def fetch_bsd_hashsum(url: str, filename: str, algo: str = "SHA256",
                       hex_len: int = 64, timeout: int = 10) -> Optional[str]:
    """
    Télécharge un fichier de sommes de contrôle au format BSD
    (ex: le fichier 'CHECKSUM' chez Fedora/Rocky/AlmaLinux, ou 'SHA512' chez
    NetBSD : "SHA256 (fichier) = empreinte") et retourne l'empreinte
    associée à `filename`, ou None si absente/injoignable.
    Le fichier peut être signé PGP en clair (clearsign, cas Fedora) : seule
    la ligne pertinente est lue, la signature n'est pas vérifiée.
    `algo` : nom de l'algorithme tel qu'il apparaît dans le fichier
    ('SHA256', 'SHA512', 'MD5'...). `hex_len` : longueur de l'empreinte.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: échec ignoré : %s", __name__, _exc)
        return None
    pattern = re.compile(
        re.escape(algo) + r"\s*\(" + re.escape(filename) + r"\)\s*=\s*([0-9a-fA-F]{" + str(hex_len) + r"})",
        re.MULTILINE,
    )
    m = pattern.search(resp.text)
    return m.group(1).lower() if m else None


def fetch_bsd_sha256(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Raccourci fetch_bsd_hashsum(algo="SHA256", hex_len=64) — voir sa docstring."""
    return fetch_bsd_hashsum(url, filename, algo="SHA256", hex_len=64, timeout=timeout)

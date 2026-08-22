"""
Generic helpers for fetching a SHA256 checksum published by an upstream
source, from a plain-text checksum file.
Used by checkers that expose a real `checksum` (as opposed to
`checksum_type` alone, which triggers no verification at all — see
core/downloader.py::download_file).

Best effort: any network/format error returns None instead of raising, so a
problem with the checksum file never causes the version check itself to
fail.
"""

import re
import requests
from typing import Optional
from core.logger import logger


def fetch_gnu_hashsum(url: str, filename: str, hex_len: int = 64, timeout: int = 10) -> Optional[str]:
    """
    Downloads a checksum file in GNU coreutils format
    (e.g. 'SHA256SUMS', 'sha512sum.txt', '<file>.sha512sum') and returns
    the checksum associated with `filename`, or None if absent/unreachable.
    Accepted formats: "<hash>  <filename>" and "<hash> *<filename>".
    `hex_len`: checksum length in hex characters (64 = sha256,
    128 = sha512, 32 = md5, 40 = sha1).
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: failed, ignored: %s", __name__, _exc)
        return None
    pattern = re.compile(
        r"^([0-9a-fA-F]{" + str(hex_len) + r"})\s+\*?(?:\./)?" + re.escape(filename) + r"\s*$",
        re.MULTILINE,
    )
    m = pattern.search(resp.text)
    return m.group(1).lower() if m else None


def fetch_sha256sums(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Shortcut for fetch_gnu_hashsum(hex_len=64) — see its docstring."""
    return fetch_gnu_hashsum(url, filename, hex_len=64, timeout=timeout)


def fetch_sha512sums(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Shortcut for fetch_gnu_hashsum(hex_len=128) — see its docstring."""
    return fetch_gnu_hashsum(url, filename, hex_len=128, timeout=timeout)


def fetch_bsd_hashsum(url: str, filename: str, algo: str = "SHA256",
                       hex_len: int = 64, timeout: int = 10) -> Optional[str]:
    """
    Downloads a checksum file in BSD format
    (e.g. the 'CHECKSUM' file used by Fedora/Rocky/AlmaLinux, or 'SHA512' on
    NetBSD: "SHA256 (file) = checksum") and returns the checksum associated
    with `filename`, or None if absent/unreachable.
    The file may be clearsigned with PGP (Fedora's case): only the relevant
    line is read, the signature itself is not verified.
    `algo`: algorithm name as it appears in the file
    ('SHA256', 'SHA512', 'MD5'...). `hex_len`: checksum length.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: failed, ignored: %s", __name__, _exc)
        return None
    pattern = re.compile(
        re.escape(algo) + r"\s*\(" + re.escape(filename) + r"\)\s*=\s*([0-9a-fA-F]{" + str(hex_len) + r"})",
        re.MULTILINE,
    )
    m = pattern.search(resp.text)
    return m.group(1).lower() if m else None


def fetch_bsd_sha256(url: str, filename: str, timeout: int = 10) -> Optional[str]:
    """Shortcut for fetch_bsd_hashsum(algo="SHA256", hex_len=64) — see its docstring."""
    return fetch_bsd_hashsum(url, filename, algo="SHA256", hex_len=64, timeout=timeout)

"""
Version checker for Mageia.
Source: https://mirrors.kernel.org/mageia/iso/ (and fallback mirrors)

Mageia no longer publishes a classic DVD since version 9: each edition
(GNOME, Plasma, Xfce) has its own subfolder containing the ISO and
verification sidecars (.md5, .sha3, .sha512). Editions are tried in the
order GNOME → Plasma → Xfce, and the published SHA512 checksum is used.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

# Mirrors to try if kernel.org is unavailable
MIRRORS = [
    "https://mirrors.kernel.org/mageia/iso/",
    "https://mirror.accum.se/mirror/mageia/iso/",
    "https://ftp.halifax.rwth-aachen.de/mageia/iso/",
]

_EDITIONS = ["GNOME", "Plasma", "Xfce"]


def _fetch_sha512(url: str, filename: str) -> Optional[str]:
    """Fetches a SHA512 checksum from a '<file>.sha512' sidecar."""
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
    except Exception:
        return None
    m = re.search(r"([0-9a-fA-F]{128})\s+\*?" + re.escape(filename), resp.text)
    return m.group(1).lower() if m else None


class MageiaChecker(BaseChecker):

    def _fetch_versions_from(self, base_url: str) -> list[int]:
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(\d+)/?"', resp.text)
            return sorted(set(int(v) for v in versions), reverse=True)
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: int, base_url: str) -> Optional[VersionInfo]:
        for edition in _EDITIONS:
            dirname = f"Mageia-{version}-Live-{edition}-x86_64"
            filename = f"{dirname}.iso"
            dir_url = f"{base_url}{version}/{dirname}/"
            url = dir_url + filename
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    checksum = _fetch_sha512(url + ".sha512", filename)
                    return VersionInfo(
                        version=str(version),
                        download_url=url,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha512",
                        variant_label=f"Live {edition}",
                    )
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                continue
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions_list = self.get_all_versions()
        return versions_list[0] if versions_list else None

    def get_all_versions(self) -> list[VersionInfo]:
        for mirror_url in MIRRORS:
            versions = self._fetch_versions_from(mirror_url)
            if not versions:
                continue
            results = []
            for v in versions:
                info = self._make_version_info(v, mirror_url)
                if info:
                    results.append(info)
            if results:
                return results
        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Mageia-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

"""
Version checker for Linux Mint.
Source: https://mirrors.edge.kernel.org/linuxmint/stable/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class LinuxMintChecker(BaseChecker):
    RELEASES_URL = "https://mirrors.edge.kernel.org/linuxmint/stable/"

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(\d+\.\d+)/?"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        variant = self.variant or "cinnamon"
        filename = f"linuxmint-{version}-{variant}-64bit.iso"
        url = f"{self.RELEASES_URL}{version}/{filename}"
        try:
            r = requests.head(url, timeout=8, allow_redirects=True)
            if r.status_code not in (200, 302):
                return None
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None
        checksum = fetch_sha256sums(f"{self.RELEASES_URL}{version}/sha256sum.txt", filename)
        return VersionInfo(
            version=version,
            download_url=url,
            filename=filename,
            checksum=checksum,
            checksum_type="sha256",
            release_notes_url="https://www.linuxmint.com/download.php",
            variant_label=variant.capitalize(),
        )

    def get_latest_version(self) -> Optional[VersionInfo]:
        for v in self._fetch_versions():
            info = self._make_version_info(v)
            if info:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        for v in self._fetch_versions():
            info = self._make_version_info(v)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"linuxmint-(\d+\.\d+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

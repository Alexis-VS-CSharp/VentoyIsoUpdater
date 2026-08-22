"""
Version checker for AlmaLinux.
Source: https://repo.almalinux.org/almalinux/
Publishes a real, generic ISO for both x86_64 and aarch64 — same repo
layout, only the "isos/<arch>/" path segment and filename change.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger

_ARCH_DIR = {"amd64": "x86_64", "arm64": "aarch64"}


class AlmaLinuxChecker(BaseChecker):
    RELEASES_URL = "https://repo.almalinux.org/almalinux/"

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(\d+(?:\.\d+)?)/?"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        arch_dir = _ARCH_DIR.get(self.arch, "x86_64")
        iso_url = f"https://repo.almalinux.org/almalinux/{version}/isos/{arch_dir}/"
        try:
            resp = requests.get(iso_url, timeout=10)
            resp.raise_for_status()
            isos = re.findall(
                rf'(AlmaLinux-{re.escape(version)}-{arch_dir}-(dvd|minimal)\.iso)',
                resp.text
            )
            if not isos:
                return None
            filename = next((f for f, t in isos if t == "dvd"), isos[0][0])
            iso_type = "DVD" if "dvd" in filename else "Minimal"
            # A single CHECKSUM file (BSD format) covers the whole directory
            checksum = fetch_bsd_sha256(iso_url + "CHECKSUM", filename)
            return VersionInfo(
                version=version,
                download_url=iso_url + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url="https://almalinux.org/blog/",
                variant_label=iso_type,
                arch=self.arch,
            )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

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
        m = re.search(r"AlmaLinux-(\d+(?:\.\d+)?)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

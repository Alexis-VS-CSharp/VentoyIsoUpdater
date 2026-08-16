"""
Vérificateur de version pour Rocky Linux.
Source : https://download.rockylinux.org/pub/rocky/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class RockyChecker(BaseChecker):
    RELEASES_URL = "https://download.rockylinux.org/pub/rocky/"

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
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        iso_url = f"https://download.rockylinux.org/pub/rocky/{version}/isos/x86_64/"
        try:
            resp = requests.get(iso_url, timeout=10)
            resp.raise_for_status()
            isos = re.findall(
                rf'(Rocky-{re.escape(version)}-x86_64-(dvd|minimal)\.iso)',
                resp.text
            )
            if not isos:
                return None
            # Préfère DVD, sinon minimal
            filename = next((f for f, t in isos if t == "dvd"), isos[0][0])
            iso_type = "DVD" if "dvd" in filename else "Minimal"
            # Chaque ISO a son propre fichier <nom>.CHECKSUM (format BSD)
            checksum = fetch_bsd_sha256(iso_url + filename + ".CHECKSUM", filename)
            return VersionInfo(
                version=version,
                download_url=iso_url + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url=f"https://rockylinux.org/news/",
                variant_label=iso_type,
            )
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
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
        m = re.search(r"Rocky-(\d+(?:\.\d+)?)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

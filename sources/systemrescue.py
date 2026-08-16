"""
Vérificateur de version pour SystemRescue.
Source : https://www.system-rescue.org/Download/ — la page officielle donne
le lien Fastly direct et le sidecar .sha256 (sur son propre domaine, pas
SourceForge).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_DOWNLOAD_PAGE = "https://www.system-rescue.org/Download/"


class SystemRescueChecker(BaseChecker):
    DOWNLOAD_PAGE = _DOWNLOAD_PAGE

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.DOWNLOAD_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            m = re.search(
                r'href="(https://fastly-cdn\.system-rescue\.org/releases/'
                r'([\d.]+)/(systemrescue-[\d.]+-amd64\.iso))"',
                resp.text
            )
            if not m:
                return []
            url, version, filename = m.group(1), m.group(2), m.group(3)
            sums_url = f"https://www.system-rescue.org/releases/{version}/{filename}.sha256"
            checksum = fetch_sha256sums(sums_url, filename)
            return [VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label="amd64",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"systemrescue-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

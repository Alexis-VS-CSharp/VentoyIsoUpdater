"""
Vérificateur de version pour Lakka.
Source : https://le.builds.lakka.tv/Generic.x86_64/ — le serveur de build
officiel liste toutes les versions avec un sidecar .sha256 par fichier ;
plus fiable que les releases GitHub (quota d'API partagé, pas d'empreinte).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_BUILDS_URL = "https://le.builds.lakka.tv/Generic.x86_64/"


class LakkaChecker(BaseChecker):
    BUILDS_URL = _BUILDS_URL

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.BUILDS_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r'href="(Lakka-Generic\.x86_64-([\d.]+)\.img\.gz)"',
                resp.text
            )
            if not matches:
                return []
            from packaging.version import Version
            matches.sort(key=lambda x: Version(x[1]), reverse=True)
            filename, version = matches[0]
            checksum = fetch_sha256sums(self.BUILDS_URL + filename + ".sha256", filename)
            return [VersionInfo(
                version=version,
                download_url=self.BUILDS_URL + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label="Generic x86_64",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Lakka-Generic\.x86_64-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

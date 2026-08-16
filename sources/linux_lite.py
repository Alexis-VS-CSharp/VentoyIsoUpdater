"""
Vérificateur de version pour Linux Lite.
Version + empreinte : https://www.linuxliteos.com/download.php (la page
officielle affiche déjà la version, le SHA256 et le MD5 en clair pour la
dernière release — pas besoin d'interroger SourceForge pour ça).
Téléchargement : SourceForge project linux-lite/files/ (mêmes fichiers).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_DOWNLOAD_PAGE = "https://www.linuxliteos.com/download.php"
_SF_BASE = "https://sourceforge.net/projects/linux-lite/files/"


class LinuxLiteChecker(BaseChecker):
    DOWNLOAD_PAGE = _DOWNLOAD_PAGE
    SF_BASE = _SF_BASE

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
            m = re.search(r"Linux Lite (\d+\.\d+)", resp.text)
            if not m:
                return []
            version = m.group(1)
            # Le bloc SHA256 suit le titre de version dans le HTML
            block = resp.text[m.end():m.end() + 3000]
            sum_m = re.search(r"SHA256\s*:\s*</strong>\s*<code[^>]*>([0-9a-fA-F]{64})", block)
            checksum = sum_m.group(1).lower() if sum_m else None
            filename = f"linux-lite-{version}-64bit.iso"
            dl_url = f"{self.SF_BASE}{version}/{filename}/download"
            return [VersionInfo(
                version=version,
                download_url=dl_url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label="64-bit",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"linux-lite-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

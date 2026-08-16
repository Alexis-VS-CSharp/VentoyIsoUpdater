"""
Vérificateur de version pour KDE Neon.
Source : https://files.kde.org/neon/images/desktop/user/current/
(chemin mis à jour : KDE a inséré un niveau "desktop/" en 2026 — l'ancien
chemin .../neon/images/user/current/ répond désormais 404).
Le fichier courant se nomme neon-user-desktop-current.iso (redirige vers la
version datée) ; un .sha256sum accompagne chaque ISO daté.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class KdeNeonChecker(BaseChecker):
    INDEX_URL = "https://files.kde.org/neon/images/desktop/user/current/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.INDEX_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(r'href="(neon-user-desktop-(\d{8}-\d+)\.iso)"', resp.text)
            if not matches:
                return []
            matches = sorted(set(matches), key=lambda x: x[1], reverse=True)
            filename, build = matches[0]
            # Le sidecar remplace ".iso" par ".sha256sum" (pas de suffixe ajouté)
            sums_name = filename[:-len(".iso")] + ".sha256sum"
            checksum = fetch_sha256sums(self.INDEX_URL + sums_name, filename)
            return [VersionInfo(
                version=build,
                download_url=self.INDEX_URL + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label="User Edition",
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"neon-user-(?:desktop-)?(\d{8}(?:-\d+)?)", filename)
        return m.group(1) if m else None

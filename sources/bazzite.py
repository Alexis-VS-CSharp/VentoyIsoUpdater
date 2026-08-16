"""
Bazzite — Fedora-based gaming distro.
Source : download.bazzite.gg (téléchargement direct, nom de fichier stable)

Le site officiel (bazzite.gg) est une page JS ("image picker") qui ne liste
aucune URL statique dans son HTML ; les vrais liens sont construits par son
script (content/themes/betheme-child/script121.js) selon le schéma :
  https://download.bazzite.gg/<image>-stable-amd64.iso
  https://download.bazzite.gg/<image>-stable-amd64.iso-CHECKSUM
Les releases GitHub (ublue-os/bazzite) ne sont plus utilisables : ce sont
désormais des builds "testing" sans ISO attaché. Le nom de fichier ne
contient pas de version — on utilise la date "Last-Modified" du fichier.
"""
import re
from datetime import datetime
from typing import Optional
import requests
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_VARIANT_IMAGE = {
    None:   "bazzite",
    "deck": "bazzite-deck",
}
_BASE = "https://download.bazzite.gg/"


class BazziteChecker(BaseChecker):

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        imagename = _VARIANT_IMAGE.get(self.variant, f"bazzite-{self.variant}" if self.variant else "bazzite")
        filename = f"{imagename}-stable-amd64.iso"
        url = _BASE + filename
        try:
            r = requests.head(url, timeout=10, allow_redirects=True)
            if r.status_code != 200:
                return []
            version = "latest"
            lm = r.headers.get("Last-Modified")
            if lm:
                try:
                    version = datetime.strptime(lm, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y.%m.%d")
                except ValueError:
                    pass
            checksum = fetch_sha256sums(url + "-CHECKSUM", filename)
            return [VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label=imagename,
            )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"bazzite.*?-v?([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

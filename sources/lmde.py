"""
Vérificateur de version pour LMDE (Linux Mint Debian Edition).
Source : miroirs officiels Linux Mint (ISO/debian/)
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

# Plusieurs miroirs à essayer
MIRRORS = [
    "https://mirror.ufscar.br/mint-cd/debian/",
    "https://muug.ca/mirror/linuxmint/iso/debian/",
    "https://ftp.rz.uni-frankfurt.de/pub/mirrors/linux-mint/iso/debian/",
    "https://mirror.bytemark.co.uk/linuxmint/debian/",
]


class LMDEChecker(BaseChecker):

    def _fetch_lmde_from_mirror(self, mirror_url: str) -> list[VersionInfo]:
        try:
            resp = requests.get(mirror_url, timeout=10)
            resp.raise_for_status()
            # Cherche les ISOs LMDE directement ou dans des sous-dossiers
            # Format: lmde-7-cinnamon-64bit.iso ou LMDE-6-cinnamon-64bit.iso
            isos = re.findall(
                r'((?:lmde|LMDE)-(\d+)-cinnamon-64bit\.iso)',
                resp.text, re.IGNORECASE
            )
            results = []
            seen = set()
            for filename, version in isos:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_sha256sums(mirror_url + "sha256sum.txt", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=mirror_url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://www.linuxmint.com/download_lmde.php",
                    variant_label="Cinnamon",
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        for mirror in MIRRORS:
            results = self._fetch_lmde_from_mirror(mirror)
            if results:
                from packaging.version import Version, InvalidVersion
                def sort_key(x):
                    try:
                        return Version(x.version)
                    except InvalidVersion:
                        return Version("0")
                results.sort(key=sort_key, reverse=True)
                return results

        # Fallback : essai direct linuxmint.com pour LMDE 7
        try:
            for ver, filename in [
                ("7", "lmde-7-cinnamon-64bit.iso"),
                ("6", "lmde-6-cinnamon-64bit.iso"),
            ]:
                url = f"https://mirror.ufscar.br/mint-cd/debian/{filename}"
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    return [VersionInfo(
                        version=ver,
                        download_url=url,
                        filename=filename,
                        release_notes_url="https://www.linuxmint.com/download_lmde.php",
                        variant_label="Cinnamon",
                    )]
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"(?:lmde|LMDE)-(\d+(?:\.\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None

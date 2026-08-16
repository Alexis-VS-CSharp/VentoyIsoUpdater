"""
Vérificateur de version pour Q4OS.
Source : https://www.q4os.org/downloads1.html

Le nom de fichier réel est "q4os-<version>-x64.r<n>.iso" (pas "-x86_64-"
comme l'ancien code l'attendait) — le téléchargement passe par un flux
"faire un don ou passer" qui redirige finalement vers SourceForge, mais la
page elle-même liste déjà le nom exact et son empreinte MD5 en clair dans
sa section "Files details", donc pas besoin de suivre ce flux.
Le WAF du site renvoie une erreur si la requête n'a pas d'en-tête
Accept-Language — un User-Agent seul ne suffit pas.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
_SF_STABLE = "https://sourceforge.net/projects/q4os/files/stable/"


class Q4OSChecker(BaseChecker):
    DL_PAGE = "https://www.q4os.org/downloads1.html"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.DL_PAGE, timeout=10, headers=_HEADERS)
            resp.raise_for_status()
            # "Files details" liste "<md5>  <fichier>" pour chaque édition
            matches = re.findall(
                r"([0-9a-fA-F]{32})\s+(q4os-([\d.]+)-x64(?:-\w+)?\.r\d+\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for checksum, filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                edition = "TDE" if "-tde." in filename else (
                    "Install CD" if "-instcd." in filename else "Plasma")
                results.append(VersionInfo(
                    version=version,
                    download_url=f"{_SF_STABLE}{filename}/download",
                    filename=filename,
                    checksum=checksum.lower(),
                    checksum_type="md5",
                    variant_label=edition,
                ))
            if results:
                from packaging.version import Version
                results.sort(key=lambda x: Version(x.version), reverse=True)
                return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"q4os-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

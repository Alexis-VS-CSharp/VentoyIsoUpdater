"""
Nobara Project — Gaming-optimized Fedora.
Source : https://nobaraproject.org/download.html

Le bouton de téléchargement ne pointe plus vers GitHub releases (plus
d'assets ISO là-bas) mais construit son lien depuis des attributs
data-iso/data-url embarqués dans la page elle-même (nobara-images.
nobaraproject.org). Chaque ISO a un sidecar "<iso>.sha256sum".
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class NobaraChecker(BaseChecker):
    DOWNLOAD_PAGE = "https://nobaraproject.org/download.html"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        edition = self.variant or "Official"
        try:
            resp = requests.get(
                self.DOWNLOAD_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            matches = re.findall(
                rf'data-iso="(Nobara-(\d+)-{re.escape(edition)}-[\d-]+\.iso)"\s+data-url="([^"]+)"',
                resp.text, re.IGNORECASE
            )
            results = []
            seen = set()
            for filename, version, url in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_sha256sums(url + ".sha256sum", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label=edition,
                ))
            results.sort(key=lambda x: x.filename, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Nobara-(\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

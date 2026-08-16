"""
Vérificateur de version pour OpenBSD.
Source : https://cdn.openbsd.org/pub/OpenBSD/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class OpenBSDChecker(BaseChecker):
    BASE_URL = "https://cdn.openbsd.org/pub/OpenBSD/"

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            # \d+ en tête : exclut le lien "dossier parent" (href="../") que
            # [\d.]+ capturerait aussi ('..' est fait uniquement de points).
            versions = re.findall(r'href="(\d+(?:\.\d+)*)/?"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        # install78.iso, install77.iso, etc.
        ver_nodot = version.replace(".", "")
        filename = f"install{ver_nodot}.iso"
        url = f"{self.BASE_URL}{version}/amd64/{filename}"
        try:
            r = requests.head(url, timeout=8, allow_redirects=True)
            if r.status_code in (200, 302):
                sums_url = f"{self.BASE_URL}{version}/amd64/SHA256"
                checksum = fetch_bsd_sha256(sums_url, filename)
                return VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="amd64",
                )
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            pass
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
        m = re.search(r"install(\d{2,})", filename)
        if m:
            digits = m.group(1)
            if len(digits) == 2:
                return f"{digits[0]}.{digits[1]}"
            return digits
        return None

"""
Vérificateur de version pour NetBSD.
Source : https://cdn.netbsd.org/pub/NetBSD/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_hashsum
from core.logger import logger


class NetBSDChecker(BaseChecker):
    BASE_URL = "https://cdn.netbsd.org/pub/NetBSD/"

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="NetBSD-([\d.]+)/"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        for iso_name in ("boot.iso", "boot-com.iso"):
            url = (f"{self.BASE_URL}NetBSD-{version}/amd64/installation/cdrom/{iso_name}")
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    cdrom_dir = f"{self.BASE_URL}NetBSD-{version}/amd64/installation/cdrom/"
                    checksum = fetch_bsd_hashsum(cdrom_dir + "SHA512", iso_name, algo="SHA512", hex_len=128)
                    return VersionInfo(
                        version=version,
                        download_url=url,
                        filename=f"NetBSD-{version}-amd64-{iso_name}",
                        checksum=checksum,
                        checksum_type="sha512",
                        variant_label="amd64",
                    )
            except Exception as _exc:
                logger.debug("%s: échec ignoré : %s", __name__, _exc)
                continue
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
        m = re.search(r"NetBSD-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

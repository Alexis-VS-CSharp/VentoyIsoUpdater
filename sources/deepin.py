"""
Version checker for Deepin.
Source: https://cdimage.deepin.com/releases/ — the project's official CDN,
which lists versions, ISOs and SHA256SUMS directly (unlike SourceForge,
used only as an alternate download link on the deepin.org/download/ page,
this CDN isn't subject to the same blocking).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_RELEASES_URL = "https://cdimage.deepin.com/releases/"


class DeepinChecker(BaseChecker):
    RELEASES_URL = _RELEASES_URL

    def _fetch_versions(self) -> list[str]:
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="([\d]+(?:\.[\d]+)*)/?"', resp.text)
            from packaging.version import Version, InvalidVersion
            unique = list(dict.fromkeys(versions))
            def sort_key(v):
                try:
                    return Version(v)
                except InvalidVersion:
                    return Version("0")
            unique.sort(key=sort_key, reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        dir_url = f"{self.RELEASES_URL}{version}/amd64/"
        filename = f"deepin-desktop-community-{version}-amd64.iso"
        try:
            r = requests.head(dir_url + filename, timeout=8, allow_redirects=True)
            if r.status_code not in (200, 302):
                return None
            checksum = fetch_sha256sums(dir_url + "SHA256SUMS", filename)
            return VersionInfo(
                version=version,
                download_url=dir_url + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label="Desktop",
            )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
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
        m = re.search(r"deepin[^\d]+([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

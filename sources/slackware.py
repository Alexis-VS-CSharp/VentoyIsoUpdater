"""
Version checker for Slackware.
Source: https://mirrors.slackware.com/slackware/slackware-iso/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_gnu_hashsum
from core.logger import logger

MIRRORS = [
    "https://mirrors.slackware.com/slackware/slackware-iso/",
    "https://mirrors.kernel.org/slackware/slackware-iso/",
]


class SlackwareChecker(BaseChecker):

    def _fetch_from_mirror(self, base_url: str) -> list[VersionInfo]:
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            # Folders like slackware64-15.0-iso/, slackware64-current-iso/
            version_dirs = re.findall(r'href="(slackware64-([\d.]+)-iso)/?"', resp.text)
            results = []
            for folder, version in version_dirs:
                filename = f"slackware64-{version}-install-dvd.iso"
                iso_url = f"{base_url}{folder}/{filename}"
                try:
                    r = requests.head(iso_url, timeout=8, allow_redirects=True)
                    if r.status_code in (200, 302):
                        checksum = fetch_gnu_hashsum(iso_url + ".md5", filename, hex_len=32)
                        results.append(VersionInfo(
                            version=version,
                            download_url=iso_url,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="md5",
                            variant_label="DVD",
                        ))
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
            from packaging.version import Version as PV, InvalidVersion
            def sort_key(x):
                try:
                    return PV(x.version)
                except InvalidVersion:
                    return PV("0")
            results.sort(key=sort_key, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        for mirror in MIRRORS:
            results = self._fetch_from_mirror(mirror)
            if results:
                return results
        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"slackware(?:64)?-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

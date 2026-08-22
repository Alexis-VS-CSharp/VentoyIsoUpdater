"""
Version checker for Gentoo (minimal install ISO).
Source: https://distfiles.gentoo.org/releases/{arch}/autobuilds/current-install-{arch}-minimal/
Publishes a real, generic ISO for both amd64 and arm64.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class GentooChecker(BaseChecker):

    def _base_url(self) -> str:
        return (f"https://distfiles.gentoo.org/releases/{self.arch}/autobuilds/"
                f"current-install-{self.arch}-minimal/")

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        base_url = self._base_url()
        try:
            resp = requests.get(base_url, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                rf"(install-{self.arch}-minimal-(\d+T\d+Z)\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_sha256sums(base_url + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=base_url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="Minimal Install",
                    arch=self.arch,
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"install-(?:amd64|arm64)-minimal-(\d+T\d+Z)", filename)
        return m.group(1) if m else None

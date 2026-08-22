"""
Version checker for Gentoo (minimal install ISO).
Source: https://distfiles.gentoo.org/releases/amd64/autobuilds/current-install-amd64-minimal/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class GentooChecker(BaseChecker):
    BASE_URL = ("https://distfiles.gentoo.org/releases/amd64/autobuilds/"
                "current-install-amd64-minimal/")

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r"(install-amd64-minimal-(\d+T\d+Z)\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_sha256sums(self.BASE_URL + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.BASE_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="Minimal Install",
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"install-amd64-minimal-(\d+T\d+Z)", filename)
        return m.group(1) if m else None

"""
Version checker for Alpine Linux.
Source: https://dl-cdn.alpinelinux.org/alpine/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class AlpineChecker(BaseChecker):
    BASE_URL = "https://dl-cdn.alpinelinux.org/alpine/"

    def _fetch_major_versions(self) -> list[str]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(v[\d.]+)/"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(versions))
            unique.sort(key=lambda v: Version(v.lstrip("v")), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _find_iso_in_release_dir(self, major: str) -> Optional[VersionInfo]:
        variant = self.variant or "standard"
        arch_url = f"{self.BASE_URL}{major}/releases/x86_64/"
        try:
            resp = requests.get(arch_url, timeout=10)
            resp.raise_for_status()
            pattern = rf"(alpine-{re.escape(variant)}-([\d.]+)-x86_64\.iso)"
            matches = re.findall(pattern, resp.text)
            if not matches:
                return None
            from packaging.version import Version
            matches.sort(key=lambda x: Version(x[1]), reverse=True)
            filename, version = matches[0]
            # Alpine publishes a real SHA256 sidecar (in addition to a GPG
            # .asc signature this project doesn't verify — see core/downloader.py)
            checksum = fetch_sha256sums(arch_url + filename + ".sha256", filename)
            return VersionInfo(
                version=version,
                download_url=arch_url + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label=variant.capitalize(),
            )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        for major in self._fetch_major_versions():
            info = self._find_iso_in_release_dir(major)
            if info:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        for major in self._fetch_major_versions():
            info = self._find_iso_in_release_dir(major)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"alpine-(?:standard|extended)-([\d.]+)-x86_64", filename, re.IGNORECASE)
        return m.group(1) if m else None

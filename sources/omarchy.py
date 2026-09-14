"""
Omarchy — opinionated Arch Linux + Hyprland desktop by DHH.
Source: GitHub releases (omacom/omarchy) for the version number, the ISO
itself is hosted on a separate domain (iso.omarchy.org) rather than as a
release asset.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class OmarchyChecker(BaseChecker):
    RELEASES_URL = "https://api.github.com/repos/omacom/omarchy/releases"
    ISO_BASE = "https://iso.omarchy.org"

    def _build_version_info(self, version: str) -> VersionInfo:
        filename = f"omarchy-{version}.iso"
        download_url = f"{self.ISO_BASE}/{filename}"
        checksum = fetch_sha256sums(f"{download_url}.sha256", filename)
        return VersionInfo(
            version=version,
            download_url=download_url,
            filename=filename,
            checksum=checksum,
            checksum_type="sha256",
            release_notes_url="https://github.com/omacom/omarchy/releases",
            variant_label="Omarchy",
        )

    def get_latest_version(self) -> Optional[VersionInfo]:
        try:
            resp = requests.get(
                f"{self.RELEASES_URL}/latest", timeout=10,
                headers={"Accept": "application/vnd.github+json"},
            )
            resp.raise_for_status()
            version = resp.json().get("tag_name", "").lstrip("v")
            if not version:
                return None
            return self._build_version_info(version)
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.RELEASES_URL, timeout=10,
                headers={"Accept": "application/vnd.github+json"},
                params={"per_page": 10},
            )
            resp.raise_for_status()
            releases = resp.json()
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

        results = []
        for release in releases:
            if release.get("prerelease") or release.get("draft"):
                continue
            version = release.get("tag_name", "").lstrip("v")
            if version:
                results.append(self._build_version_info(version))
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"omarchy-([\d.]+)\.iso", filename, re.IGNORECASE)
        return m.group(1) if m else None

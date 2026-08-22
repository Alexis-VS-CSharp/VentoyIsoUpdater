"""
Version checker for VanillaOS.
Source: GitHub releases Vanilla-OS/live-iso
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_API = "https://api.github.com/repos/Vanilla-OS/live-iso/releases"


class VanillaOSChecker(BaseChecker):

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                _API, timeout=12,
                headers={"Accept": "application/vnd.github+json",
                         "X-GitHub-Api-Version": "2022-11-28"},
                params={"per_page": 10},
            )
            resp.raise_for_status()
            releases = resp.json()
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

        results = []
        for release in releases:
            if release.get("draft"):
                continue
            version = release.get("tag_name", "").lstrip("v")
            assets = release.get("assets", [])
            sums_asset = next(
                (a for a in assets if a.get("name", "").endswith(".sha256.txt")), None
            )
            for asset in assets:
                name = asset.get("name", "")
                if re.search(r"VanillaOS[^\"]*\.iso$", name, re.IGNORECASE):
                    checksum = None
                    if sums_asset:
                        checksum = fetch_sha256sums(sums_asset["browser_download_url"], name)
                    results.append(VersionInfo(
                        version=version,
                        download_url=asset["browser_download_url"],
                        filename=name,
                        checksum=checksum,
                        checksum_type="sha256",
                        variant_label="VanillaOS",
                    ))
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"VanillaOS[_-]([\d.]+)", filename, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"vanilla[_-]os[_-]?([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

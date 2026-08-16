"""ChimeraOS — Gaming Linux console OS.
GitHub: ChimeraOS/chimeraos (images en .img.tar.xz, pas .iso)
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class ChimeraOSChecker(BaseChecker):
    RELEASES_URL = "https://api.github.com/repos/ChimeraOS/chimeraos/releases"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            resp = requests.get(
                self.RELEASES_URL,
                timeout=12,
                headers=headers,
                params={"per_page": 8},
            )
            resp.raise_for_status()
            releases = resp.json()
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

        results = []
        for release in releases:
            if release.get("prerelease") or release.get("draft"):
                continue
            tag = release.get("tag_name", "")
            version = tag.lstrip("v")
            assets = release.get("assets", [])
            sums_asset = next((a for a in assets if a.get("name") == "sha256sum.txt"), None)
            for asset in assets:
                name = asset.get("name", "")
                # ChimeraOS distribue en .img.tar.xz
                if re.search(r"chimeraos.*\.(img\.tar\.xz|iso)$", name, re.IGNORECASE):
                    checksum = None
                    if sums_asset:
                        checksum = fetch_sha256sums(sums_asset["browser_download_url"], name)
                    results.append(VersionInfo(
                        version=version,
                        download_url=asset["browser_download_url"],
                        filename=name,
                        checksum=checksum,
                        checksum_type="sha256",
                        variant_label="Gaming Console OS",
                    ))
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"chimeraos[_-](\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

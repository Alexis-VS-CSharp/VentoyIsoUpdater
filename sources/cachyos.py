"""
Version checker for CachyOS.
Source: GitHub releases CachyOS/cachyos-live-iso
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._github import get_github_iso_releases
from sources._checksum import fetch_sha256sums
from core.logger import logger


class CachyOSChecker(BaseChecker):

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        # Attempt 1: GitHub releases CachyOS/cachyos-live-iso
        results = get_github_iso_releases(
            owner="CachyOS",
            repo="cachyos-live-iso",
            asset_pattern=r"cachyos-.*\.iso$",
            variant_label=self.variant or "Desktop",
            max_releases=6,
        )
        if results:
            return results

        # Attempt 2: GitHub releases CachyOS/CachyOS-ISO
        results = get_github_iso_releases(
            owner="CachyOS",
            repo="CachyOS-ISO",
            asset_pattern=r"cachyos.*\.iso$",
            variant_label=self.variant or "Desktop",
            max_releases=6,
        )
        if results:
            return results

        # Attempt 3: official mirror — real structure: ISO/desktop/<YYMMDD>/
        # (the mirror lists dated subfolders, not the ISOs directly at the
        # root). Each ISO has a ".sha256" sidecar.
        try:
            mirror_url = "https://mirror.cachyos.org/ISO/desktop/"
            resp = requests.get(mirror_url, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            dates = sorted(set(re.findall(r'href="(\d{6})/"', resp.text)), reverse=True)
            for build_date in dates[:5]:
                build_url = f"{mirror_url}{build_date}/"
                try:
                    r2 = requests.get(build_url, timeout=8,
                                      headers={"User-Agent": "Mozilla/5.0"})
                    r2.raise_for_status()
                    m = re.search(r'href="(cachyos-desktop-linux-\d+\.iso)"', r2.text)
                    if not m:
                        continue
                    filename = m.group(1)
                    checksum = fetch_sha256sums(build_url + filename + ".sha256", filename)
                    return [VersionInfo(
                        version=build_date,
                        download_url=build_url + filename,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha256",
                        variant_label=self.variant or "Desktop",
                    )]
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"cachyos[^\d]*(\d{6,8})", filename, re.IGNORECASE)
        return m.group(1) if m else None

"""
Vérificateur de version pour Void Linux.
Source : https://repo-default.voidlinux.org/live/current/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class VoidLinuxChecker(BaseChecker):
    BASE_URL = "https://repo-default.voidlinux.org/live/current/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "glibc"
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()

            if variant == "musl":
                # Nouveau nommage : "musl" précède la date (ex: void-live-
                # x86_64-musl-20250202-base.iso), plus l'ancien -date-musl.iso
                pattern = r"(void-live-x86_64-musl-(\d+)(?:-(?:base|xfce))?\.iso)"
            else:
                # void-live-x86_64-20250202-base.iso ou
                # void-live-x86_64-20250202-xfce.iso ou
                # void-live-x86_64-20250202.iso (ancien format)
                pattern = r"(void-live-x86_64-(\d+)(?:-(?:base|xfce|mate|cinnamon|enlightenment|lxde|lxqt))?\.iso)"

            matches = re.findall(pattern, resp.text)
            seen_dates = set()
            results = []
            for filename, date in matches:
                if date in seen_dates:
                    continue
                seen_dates.add(date)
                checksum = fetch_bsd_sha256(self.BASE_URL + "sha256sum.txt", filename)
                results.append(VersionInfo(
                    version=date,
                    download_url=self.BASE_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label=variant,
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"void-live-x86_64-(\d+)", filename)
        return m.group(1) if m else None

"""
Version checker for Void Linux.
Source: https://repo-default.voidlinux.org/live/current/
Publishes a real, generic ISO for both x86_64 and aarch64 (musl and glibc
variants exist for both).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger

_ARCH_DIR = {"amd64": "x86_64", "arm64": "aarch64"}


class VoidLinuxChecker(BaseChecker):
    BASE_URL = "https://repo-default.voidlinux.org/live/current/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "glibc"
        arch_dir = _ARCH_DIR.get(self.arch, "x86_64")
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()

            if variant == "musl":
                # New naming: "musl" precedes the date (e.g. void-live-
                # x86_64-musl-20250202-base.iso), plus the old -date-musl.iso
                pattern = rf"(void-live-{arch_dir}-musl-(\d+)(?:-(?:base|xfce))?\.iso)"
            else:
                # void-live-x86_64-20250202-base.iso or
                # void-live-x86_64-20250202-xfce.iso or
                # void-live-x86_64-20250202.iso (old format)
                pattern = rf"(void-live-{arch_dir}-(\d+)(?:-(?:base|xfce|mate|cinnamon|enlightenment|lxde|lxqt))?\.iso)"

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
                    arch=self.arch,
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"void-live-(?:x86_64|aarch64)-(?:musl-)?(\d+)", filename)
        return m.group(1) if m else None

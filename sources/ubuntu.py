"""
Version checker for Ubuntu (Desktop and Server).
Source: https://releases.ubuntu.com/
Server publishes a real, generic arm64 ISO too; Desktop currently doesn't
at this location (only x86_64 classic installer ISOs) — requesting
arch="arm64" with variant="desktop" simply finds nothing (all HEAD checks
404) and returns None, same as any other genuinely unavailable combination.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class UbuntuChecker(BaseChecker):
    BASE_URL = "https://releases.ubuntu.com/"

    def _fetch_versions(self) -> list[str]:
        """Fetches every version available on releases.ubuntu.com."""
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            raw = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/?"', resp.text)
            from packaging.version import Version
            # Sorts while keeping the original string (packaging normalizes and breaks URLs)
            unique = list(dict.fromkeys(raw))  # deduplicates while keeping order
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        variant = self.variant or "desktop"

        if variant == "server":
            candidates = [
                (f"ubuntu-{version}-live-server-{self.arch}.iso", "Server"),
                (f"ubuntu-{version}-server-{self.arch}.iso",      "Server"),
            ]
        else:
            candidates = [
                (f"ubuntu-{version}-desktop-{self.arch}.iso",     "Desktop"),
                (f"ubuntu-{version}-desktop-legacy-{self.arch}.iso", "Desktop (legacy)"),
            ]

        # LTS = xx.04 versions (stable), xx.10 = interim (non-LTS)
        minor = version.split(".")[1] if "." in version else "0"
        is_lts = minor == "04"

        for filename, variant_label in candidates:
            url = f"{self.BASE_URL}{version}/{filename}"
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    lbl = variant_label + (" LTS" if is_lts else "")
                    checksum = fetch_sha256sums(f"{self.BASE_URL}{version}/SHA256SUMS", filename)
                    return VersionInfo(
                        version=version,
                        download_url=url,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha256",
                        release_notes_url="https://wiki.ubuntu.com/Releases",
                        variant_label=lbl,
                        stable=is_lts,
                        arch=self.arch,
                    )
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                continue
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self._fetch_versions()
        # Prioritizes LTS versions (xx.04) — tried first
        lts = [v for v in versions if len(v.split(".")) >= 2 and v.split(".")[1] == "04"]
        for v in lts + [v for v in versions if v not in lts]:
            info = self._make_version_info(v)
            if info and info.stable:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        versions = self._fetch_versions()
        results = []
        for v in versions:
            info = self._make_version_info(v)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"ubuntu-(\d+\.\d+(?:\.\d+)?)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

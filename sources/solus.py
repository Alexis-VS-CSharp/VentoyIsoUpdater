"""
Version checker for Solus.
Source: https://getsol.us/download/ (link resolution) then
https://downloads.getsol.us/isos/<date>/ (actual files + .sha256sum sidecars).

The download page now only exposes magnet links — the direct HTTP link is
present inside them as the "ws=" (webseed) parameter: that's the one
extracted, rather than the magnet link itself.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_gnu_hashsum
from core.logger import logger


class SolusChecker(BaseChecker):
    DOWNLOAD_URL = "https://getsol.us/download/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        edition = self.variant or "Budgie"

        try:
            resp = requests.get(
                self.DOWNLOAD_URL,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()

            # The real HTTP link is the ws= parameter of this edition's magnet link
            m = re.search(
                rf'ws=(https://downloads\.getsol\.us/isos/[^&"]+/Solus-{re.escape(edition)}-Release-[^&"]+\.iso)',
                resp.text, re.IGNORECASE
            )
            if not m:
                return []
            url = m.group(1).replace("&amp;", "&")
            filename = url.split("/")[-1]
            version_m = re.search(r"Release-([\d-]+)\.iso", filename)
            version = version_m.group(1) if version_m else "latest"

            checksum = fetch_gnu_hashsum(url + ".sha256sum", filename, hex_len=64)
            return [VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                variant_label=edition,
            )]
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Solus-[A-Za-z]+-Release-([\d-]+)", filename, re.IGNORECASE)
        if m:
            return m.group(1)
        m = re.search(r"Solus-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

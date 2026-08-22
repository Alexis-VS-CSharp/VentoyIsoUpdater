"""
Version checker for Peppermint OS.
Source: https://peppermintos.com/trixie-base-downloads/ — the official page
references both SourceForge and a direct mirror (OSSPlanet, not subject to
SourceForge's occasional anti-bot blocking) with its SHA512 checksum right
next to it.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_gnu_hashsum
from core.logger import logger

_DOWNLOAD_PAGE = "https://peppermintos.com/trixie-base-downloads/"
_MIRROR = "https://mirror.ossplanet.net/peppermint/iso/XFCE/PeppermintOS-Debian-64.iso"


class PeppermintChecker(BaseChecker):
    DOWNLOAD_PAGE = _DOWNLOAD_PAGE

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            r = requests.head(_MIRROR, timeout=10, allow_redirects=True)
            if r.status_code not in (200, 302):
                return []
            filename = _MIRROR.split("/")[-1]
            sums_url = _MIRROR.rsplit(".", 1)[0] + "-sha512.checksum"
            checksum = fetch_gnu_hashsum(sums_url, filename, hex_len=128)
            lm = r.headers.get("Last-Modified")
            version = "latest"
            if lm:
                from datetime import datetime
                try:
                    version = datetime.strptime(
                        lm, "%a, %d %b %Y %H:%M:%S %Z"
                    ).strftime("%Y.%m.%d")
                except ValueError:
                    pass
            return [VersionInfo(
                version=version,
                download_url=_MIRROR,
                filename=filename,
                checksum=checksum,
                checksum_type="sha512",
                variant_label="Debian Base",
            )]
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"[Pp]eppermint[_-]?[Oo][Ss]?-?[Dd]ebian-(\d+(?:\.\d+)*)", filename)
        if m:
            return m.group(1)
        m = re.search(r"(\d{4}\.\d{2}\.\d{2})", filename)
        return m.group(1) if m else None

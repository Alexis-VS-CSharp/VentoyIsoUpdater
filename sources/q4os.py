"""
Version checker for Q4OS.
Source: https://www.q4os.org/downloads1.html

The real filename is "q4os-<version>-x64.r<n>.iso" (not "-x86_64-" as the
old code expected) — the download goes through a "donate or skip" flow
that eventually redirects to SourceForge, but the page itself already
lists the exact name and its MD5 checksum in plain text in its "Files
details" section, so there's no need to follow that flow.
The site's WAF returns an error if the request has no Accept-Language
header — a User-Agent alone isn't enough.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
_SF_STABLE = "https://sourceforge.net/projects/q4os/files/stable/"


class Q4OSChecker(BaseChecker):
    DL_PAGE = "https://www.q4os.org/downloads1.html"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.DL_PAGE, timeout=10, headers=_HEADERS)
            resp.raise_for_status()
            # "Files details" lists "<md5>  <file>" for each edition
            matches = re.findall(
                r"([0-9a-fA-F]{32})\s+(q4os-([\d.]+)-x64(?:-\w+)?\.r\d+\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for checksum, filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                edition = "TDE" if "-tde." in filename else (
                    "Install CD" if "-instcd." in filename else "Plasma")
                results.append(VersionInfo(
                    version=version,
                    download_url=f"{_SF_STABLE}{filename}/download",
                    filename=filename,
                    checksum=checksum.lower(),
                    checksum_type="md5",
                    variant_label=edition,
                ))
            if results:
                from packaging.version import Version
                results.sort(key=lambda x: Version(x.version), reverse=True)
                return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)

        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"q4os-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

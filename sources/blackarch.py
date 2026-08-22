"""
Version checker for BlackArch Linux.
Source: https://blackarch.org/downloads.html — the official page lists
the "Full" ISO (real URL on the ftp.halifax.rwth-aachen.de mirror) with its
SHA1 checksum directly in the HTML table (no separate file).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


class BlackArchChecker(BaseChecker):
    DOWNLOADS_PAGE = "https://blackarch.org/downloads.html"
    # Fallback mirror if the official page is unreachable (no checksum then)
    MIRROR_URL = "https://ftp.halifax.rwth-aachen.de/blackarch/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.DOWNLOADS_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            # The "Image | Version | Torrent | Size | SHA1sum" table lists
            # the ISO URL then, on the same row, its SHA1 checksum.
            m = re.search(
                r'href="([^"]*blackarch-linux-full-(\d{4}\.\d{2}\.\d{2})-x86_64\.iso)"'
                r'.*?<td>([0-9a-fA-F]{40})</td>',
                resp.text, re.DOTALL
            )
            if m:
                url, version, checksum = m.group(1), m.group(2), m.group(3)
                return [VersionInfo(
                    version=version,
                    download_url=url,
                    filename=url.split("/")[-1],
                    checksum=checksum.lower(),
                    checksum_type="sha1",
                    variant_label="Full",
                )]
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)

        # Fallback: direct mirror listing (no checksum available here)
        try:
            resp = requests.get(self.MIRROR_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r"(blackarch-linux-full-(\d{4}\.\d{2}\.\d{2})-x86_64\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.MIRROR_URL + filename,
                    filename=filename,
                    variant_label="Full",
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"blackarch[^\-]*-(\d{4}\.\d{2}\.\d{2})", filename, re.IGNORECASE)
        return m.group(1) if m else None

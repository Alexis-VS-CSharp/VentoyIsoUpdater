"""
Version checker for Memtest86 / Memtest86+.
Sources:
  - Memtest86 (PassMark): https://www.memtest86.com/download.htm
  - Memtest86+ (open source): https://www.memtest.org/ (the GitHub releases
    at memtest86plus/memtest86plus no longer have an ISO asset, just source code)
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class Memtest86PlusChecker(BaseChecker):
    # Memtest86 PassMark (commercial, free)
    PASSMARK_URL = "https://www.memtest86.com/download.htm"
    # Memtest86+ open source — the GitHub releases no longer have ISO
    # assets attached (source code only); the real binary is on memtest.org.
    MEMTEST_ORG_URL = "https://www.memtest.org/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []

        # Source 1: Memtest86 PassMark (memtest86.com)
        try:
            resp = requests.get(
                self.PASSMARK_URL, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            # Looks for download links (ZIP containing the ISO/USB image)
            links = re.findall(
                r'href="([^"]*memtest86[^"]*(?:usb|iso)\.zip)"',
                resp.text, re.IGNORECASE
            )
            for url in links[:2]:
                if not url.startswith("http"):
                    url = "https://www.memtest86.com/" + url.lstrip("/")
                filename = url.split("/")[-1].split("?")[0]
                m = re.search(r"memtest86[_-]?([\d.]+)", filename, re.IGNORECASE)
                version = m.group(1) if m else "latest"
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    variant_label="Memtest86 USB/ISO",
                    release_notes_url="https://www.memtest86.com/whats-new.htm",
                ))
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        # Source 2: Memtest86+ open source (memtest.org — the homepage
        # always references the latest stable version's link)
        try:
            resp = requests.get(
                self.MEMTEST_ORG_URL, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            m = re.search(
                r'href="(/download/(v[\d.]+)/(mt86plus_[\d.]+_x86_64\.iso\.zip))"',
                resp.text
            )
            if m:
                path, ver_dir, filename = m.group(1), m.group(2), m.group(3)
                version = ver_dir.lstrip("v")
                url = self.MEMTEST_ORG_URL.rstrip("/") + path
                checksum = fetch_sha256sums(
                    f"{self.MEMTEST_ORG_URL}download/{ver_dir}/sha256sum.txt",
                    f"{ver_dir}/{filename}",
                )
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="Memtest86+",
                ))
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"memtest86\+?[_-]?([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

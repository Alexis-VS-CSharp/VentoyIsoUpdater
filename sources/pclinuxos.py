"""
Version checker for PCLinuxOS.
Source: NLUUG mirror or SourceForge

The NLUUG path contained an extra "pclinuxos/" segment (.../pclinuxos/
pclinuxos/iso/, which doesn't exist) and the expected filename was the old
format "pclinuxos-kde-<build>-x86_64.iso": the real naming is now
"pclinuxos64-kde-<date>.iso", with a ".md5sum" sidecar.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_gnu_hashsum
from core.logger import logger

MIRRORS = [
    "https://ftp.nluug.nl/os/Linux/distr/pclinuxos/iso/",
    "https://sourceforge.net/projects/pclinuxos/files/pclinuxos/KDE/",
]


class PCLinuxOSChecker(BaseChecker):

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        # Attempt 1: NLUUG mirror (direct listing)
        try:
            mirror_url = MIRRORS[0]
            resp = requests.get(mirror_url, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r"(pclinuxos64-(kde|mate|xfce)-([\d.]+)\.iso)",
                resp.text, re.IGNORECASE
            )
            seen = set()
            results = []
            for filename, edition, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_gnu_hashsum(mirror_url + filename + ".md5sum", filename, hex_len=32)
                results.append(VersionInfo(
                    version=version,
                    download_url=mirror_url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="md5",
                    variant_label=edition.upper(),
                ))
            if results:
                results.sort(key=lambda x: x.version, reverse=True)
                return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        # Attempt 2: SourceForge (via User-Agent + HTML scraping)
        try:
            sf_url = MIRRORS[1]
            resp = requests.get(
                sf_url,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            matches = re.findall(
                r"(pclinuxos-kde-(\d+)-x86_64\.iso)",
                resp.text, re.IGNORECASE
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                dl_url = (
                    f"https://sourceforge.net/projects/pclinuxos/files/"
                    f"pclinuxos/KDE/{filename}/download"
                )
                results.append(VersionInfo(
                    version=version,
                    download_url=dl_url,
                    filename=filename,
                    variant_label="KDE",
                ))
            results.sort(key=lambda x: x.version, reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"pclinuxos64?[^-]*-(?:[a-z]+-)?([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

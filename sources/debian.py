"""
Version checker for Debian.
Source: https://cdimage.debian.org/debian-cd/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class DebianChecker(BaseChecker):
    CURRENT_URL = "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/"
    ARCHIVE_URL = "https://cdimage.debian.org/cdimage/archive/"

    def _parse_iso_list(self, url: str, variant_label: str) -> list[VersionInfo]:
        results = []
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r'(debian-(\d+\.\d+(?:\.\d+)?)-amd64-(netinst|DVD-1)\.iso)',
                resp.text
            )
            for filename, version, iso_type in matches:
                checksum = fetch_sha256sums(url + "SHA256SUMS", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://www.debian.org/releases/stable/releasenotes",
                    variant_label=f"{variant_label} ({iso_type})",
                ))
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass
        return results

    def get_latest_version(self) -> Optional[VersionInfo]:
        items = self._parse_iso_list(self.CURRENT_URL, "Stable")
        if not items:
            return None
        from packaging.version import Version
        return max(items, key=lambda x: Version(x.version))

    def get_all_versions(self) -> list[VersionInfo]:
        results = []

        # Current stable version
        results.extend(self._parse_iso_list(self.CURRENT_URL, "Stable"))

        # Archives: debian 10, 11, 12, etc.
        try:
            resp = requests.get(self.ARCHIVE_URL, timeout=10)
            resp.raise_for_status()
            archive_versions = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/?"', resp.text)
            from packaging.version import Version
            archive_versions = sorted(
                set(archive_versions), key=lambda v: Version(v), reverse=True
            )
            for av in archive_versions[:12]:  # Last 12 archived versions
                url = f"{self.ARCHIVE_URL}{av}/amd64/iso-cd/"
                results.extend(self._parse_iso_list(url, f"Archive {av}"))
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        # Deduplicate by version+filename
        seen = set()
        unique = []
        for r in results:
            key = r.filename
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"debian-(\d+\.\d+(?:\.\d+)?)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

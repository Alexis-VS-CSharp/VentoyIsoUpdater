"""
Vérificateur de version pour CentOS Stream.
Source : https://mirror.stream.centos.org/{stream}-stream/BaseOS/x86_64/iso/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class CentOSStreamChecker(BaseChecker):

    def _stream_version(self) -> str:
        return self.variant or "9"

    def _iso_dir_url(self) -> str:
        sv = self._stream_version()
        return f"https://mirror.stream.centos.org/{sv}-stream/BaseOS/x86_64/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        sv = self._stream_version()
        iso_dir = self._iso_dir_url()
        try:
            resp = requests.get(iso_dir, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r"(CentOS-Stream-(\d+)-latest-x86_64-dvd1\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_bsd_sha256(iso_dir + filename + ".SHA256SUM", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=iso_dir + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label=f"Stream {sv}",
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"CentOS-Stream-(\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

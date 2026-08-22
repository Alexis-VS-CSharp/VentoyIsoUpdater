"""
Version checker for CentOS Stream.
Source: https://mirror.stream.centos.org/{stream}-stream/BaseOS/{arch}/iso/
Publishes a real, generic ISO for both x86_64 and aarch64.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger

_ARCH_DIR = {"amd64": "x86_64", "arm64": "aarch64"}


class CentOSStreamChecker(BaseChecker):

    def _stream_version(self) -> str:
        return self.variant or "9"

    def _iso_dir_url(self) -> str:
        sv = self._stream_version()
        arch_dir = _ARCH_DIR.get(self.arch, "x86_64")
        return f"https://mirror.stream.centos.org/{sv}-stream/BaseOS/{arch_dir}/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        sv = self._stream_version()
        arch_dir = _ARCH_DIR.get(self.arch, "x86_64")
        iso_dir = self._iso_dir_url()
        try:
            resp = requests.get(iso_dir, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                rf"(CentOS-Stream-(\d+)-latest-{arch_dir}-dvd1\.iso)",
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
                    arch=self.arch,
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"CentOS-Stream-(\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

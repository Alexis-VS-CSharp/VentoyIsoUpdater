"""
Version checker for Oracle Linux.
Source: https://yum.oracle.com/oracle-linux-isos.html
Checksums: https://linux.oracle.com/security/gpg/checksum/ (see
https://linux.oracle.com/security/gpg/ for the official procedure —
clearsigned PGP file, only the SHA256 line is read).
Publishes a real, generic ISO for both x86_64 and aarch64.
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_CHECKSUM_BASE = "https://linux.oracle.com/security/gpg/checksum/"
_ARCH_DIR = {"amd64": "x86_64", "arm64": "aarch64"}


class OracleLinuxChecker(BaseChecker):
    ISOS_PAGE = "https://yum.oracle.com/oracle-linux-isos.html"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        arch_dir = _ARCH_DIR.get(self.arch, "x86_64")
        try:
            resp = requests.get(
                self.ISOS_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            # The real filename does NOT contain "-Server-" (e.g.
            # OracleLinux-R9-U8-x86_64-dvd.iso); only the checksum file is
            # named "...-Server-x86_64.checksum".
            matches = re.findall(
                rf'href="([^"]+OracleLinux-R(\d+)-U(\d+)-{arch_dir}-dvd\.iso)"',
                resp.text
            )
            seen = set()
            results = []
            for url, major, minor in matches:
                if url in seen:
                    continue
                seen.add(url)
                filename = url.split("/")[-1]
                version = f"{major}.{minor}"
                sums_url = f"{_CHECKSUM_BASE}OracleLinux-R{major}-U{minor}-Server-{arch_dir}.checksum"
                checksum = fetch_sha256sums(sums_url, filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label=f"OL{major}U{minor}",
                    arch=self.arch,
                ))
            from packaging.version import Version
            results.sort(key=lambda x: Version(x.version), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"OracleLinux-R(\d+)-U(\d+)", filename, re.IGNORECASE)
        if m:
            return f"{m.group(1)}.{m.group(2)}"
        return None

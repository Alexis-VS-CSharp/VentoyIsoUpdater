"""
Proxmox VE — bare-metal virtualization.
Source: enterprise.proxmox.com (official HTTPS mirror — download.proxmox.com
doesn't present a valid TLS certificate for its own hostname and is
therefore only reachable over HTTP; enterprise.proxmox.com serves the same
ISOs with a correct certificate and a .sha256 checksum per file).
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class ProxmoxChecker(BaseChecker):
    INDEX_URL = "https://enterprise.proxmox.com/iso/"

    def _fetch_isos(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.INDEX_URL, timeout=10)
            resp.raise_for_status()
            # The directory also lists arm64 builds (e.g. proxmox-ve_9.2-1-arm64.iso) —
            # the \.iso$ anchored right after the version number already excludes
            # that suffix (arm64 wouldn't match it), but it's also re-checked
            # explicitly as a safety net, and deduplicated (the HTML repeats each
            # filename several times: link, size, date).
            matches = re.findall(
                r'(proxmox-ve_(\d+\.\d+(?:-\d+)?)\.iso)(?!\w)',
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen or "arm" in filename.lower():
                    continue
                seen.add(filename)
                checksum = fetch_sha256sums(self.INDEX_URL + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.INDEX_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://pve.proxmox.com/wiki/Roadmap",
                    variant_label="Proxmox VE",
                    arch="amd64",
                ))
            # Descending sort by version
            from packaging.version import Version
            results.sort(key=lambda v: Version(v.version.replace("-", ".")), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def get_latest_version(self) -> Optional[VersionInfo]:
        isos = self._fetch_isos()
        return isos[0] if isos else None

    def get_all_versions(self) -> list[VersionInfo]:
        return self._fetch_isos()

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"proxmox-ve_(\d+\.\d+(?:-\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None

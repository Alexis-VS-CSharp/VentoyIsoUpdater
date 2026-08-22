"""
Proxmox VE — bare-metal virtualization.
Source: enterprise.proxmox.com (official HTTPS mirror — download.proxmox.com
doesn't present a valid TLS certificate for its own hostname and is
therefore only reachable over HTTP; enterprise.proxmox.com serves the same
ISOs with a correct certificate and a .sha256 checksum per file).
Also publishes a real, generic arm64 ISO (suffixed "-arm64" in the
filename, e.g. proxmox-ve_9.2-1-arm64.iso vs proxmox-ve_9.2-1.iso for amd64).
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
            if self.arch == "arm64":
                # e.g. proxmox-ve_9.2-1-arm64.iso
                pattern = r'(proxmox-ve_(\d+\.\d+(?:-\d+)?)-arm64\.iso)'
            else:
                # e.g. proxmox-ve_9.2-1.iso — \.iso$ anchored right after
                # the version number so it can't accidentally swallow the
                # "-arm64" suffix (there's no in-between it could match).
                pattern = r'(proxmox-ve_(\d+\.\d+(?:-\d+)?)\.iso)(?!\w)'
            matches = re.findall(pattern, resp.text)
            # The HTML repeats each filename several times (link, size,
            # date) — deduplicated here rather than trusting a single pass.
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
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
                    arch=self.arch,
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

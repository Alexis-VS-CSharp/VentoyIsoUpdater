"""
Proxmox VE — Virtualisation bare-metal.
Source : enterprise.proxmox.com (miroir HTTPS officiel — download.proxmox.com
ne présente pas de certificat TLS valide pour son propre nom d'hôte et n'est
donc joignable qu'en HTTP ; enterprise.proxmox.com sert les mêmes ISO avec un
certificat correct et une empreinte .sha256 par fichier).
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
            matches = re.findall(
                r'(proxmox-ve_(\d+\.\d+(?:-\d+)?)\.iso)',
                resp.text
            )
            results = []
            for filename, version in matches:
                checksum = fetch_sha256sums(self.INDEX_URL + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.INDEX_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://pve.proxmox.com/wiki/Roadmap",
                    variant_label="Proxmox VE",
                ))
            # Tri décroissant par version
            from packaging.version import Version
            results.sort(key=lambda v: Version(v.version.replace("-", ".")), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def get_latest_version(self) -> Optional[VersionInfo]:
        isos = self._fetch_isos()
        return isos[0] if isos else None

    def get_all_versions(self) -> list[VersionInfo]:
        return self._fetch_isos()

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"proxmox-ve_(\d+\.\d+(?:-\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None

"""OPNsense — Firewall/Router OS. Source : mirror.ams1.nl.leaseweb.net"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class OPNsenseChecker(BaseChecker):
    # variant: 'dvd' ou 'vga' (nano/serial)
    MIRROR_URL = "https://mirror.ams1.nl.leaseweb.net/opnsense/releases/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "dvd"
        try:
            resp = requests.get(self.MIRROR_URL, timeout=10)
            resp.raise_for_status()

            dirs = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/?"', resp.text)
            from packaging.version import Version as PV
            unique = list(dict.fromkeys(dirs))
            unique.sort(key=lambda v: PV(v), reverse=True)

            results = []
            for ver in unique[:6]:
                iso_url = f"{self.MIRROR_URL}{ver}/"
                try:
                    r2 = requests.get(iso_url, timeout=8)
                    r2.raise_for_status()
                    isos = re.findall(
                        rf'(OPNsense-{re.escape(ver)}-{re.escape(variant)}-amd64\.iso(?:\.bz2)?)',
                        r2.text
                    )
                    for filename in isos[:1]:
                        # Un seul fichier de checksums couvre toutes les
                        # variantes (dvd/nano/serial/vga) d'une version.
                        sums_url = f"{iso_url}OPNsense-{ver}-checksums-amd64.sha256"
                        checksum = fetch_bsd_sha256(sums_url, filename)
                        results.append(VersionInfo(
                            version=ver,
                            download_url=iso_url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url=f"https://opnsense.org/blog/",
                            variant_label=f"{variant.upper()} {ver}",
                        ))
                except Exception as _exc:
                    logger.debug("%s: échec ignoré : %s", __name__, _exc)
                    continue
            return results
        except Exception as _exc:
            logger.debug("%s: échec ignoré : %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"OPNsense-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

"""FreeBSD. Source: download.freebsd.org"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class FreeBSDChecker(BaseChecker):
    # New path since FreeBSD 14+
    RELEASES_URL = "https://download.freebsd.org/releases/amd64/amd64/ISO-IMAGES/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.RELEASES_URL, timeout=10)
            resp.raise_for_status()

            # Version folders: 14.0/, 15.0/, etc.
            # Leading \d+: excludes the "parent folder" link (href="../")
            # which [\d.]+ would also capture ('..' is made only of dots).
            dirs = re.findall(r'href="(\d+(?:\.\d+)*)/?"', resp.text)
            from packaging.version import Version as PV
            unique = list(dict.fromkeys(dirs))
            unique.sort(key=lambda v: PV(v), reverse=True)

            results = []
            for ver in unique[:5]:
                iso_url = f"{self.RELEASES_URL}{ver}/"
                try:
                    r2 = requests.get(iso_url, timeout=8)
                    r2.raise_for_status()
                    # Looks for disc1.iso or dvd1.iso
                    isos = re.findall(
                        r'(FreeBSD-[\d.]+-RELEASE-amd64-(?:disc1|dvd1)\.iso)',
                        r2.text
                    )
                    if not isos:
                        isos = re.findall(
                            r'(FreeBSD-[\d.]+-RELEASE-amd64-(?:memstick|bootonly)\.iso)',
                            r2.text
                        )
                    for filename in isos[:1]:
                        m = re.search(r'FreeBSD-([\d.]+-RELEASE)', filename)
                        rel = m.group(1) if m else ver
                        sums_url = f"{iso_url}CHECKSUM.SHA256-FreeBSD-{rel}-amd64"
                        checksum = fetch_bsd_sha256(sums_url, filename)
                        results.append(VersionInfo(
                            version=rel,
                            download_url=iso_url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url="https://www.freebsd.org/releases/",
                            variant_label="disc1",
                        ))
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"FreeBSD-([\d.]+-RELEASE)", filename, re.IGNORECASE)
        return m.group(1) if m else None

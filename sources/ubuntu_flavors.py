"""
Version checker for the official Ubuntu flavors.
Source: https://cdimage.ubuntu.com/{flavor}/releases/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

_FLAVOR_MAP = {
    "kubuntu":        ("kubuntu",        "kubuntu-{ver}-desktop-amd64.iso",     "Desktop"),
    "xubuntu":        ("xubuntu",        "xubuntu-{ver}-desktop-amd64.iso",     "Desktop"),
    "lubuntu":        ("lubuntu",        "lubuntu-{ver}-desktop-amd64.iso",     "Desktop"),
    "ubuntu-mate":    ("ubuntu-mate",    "ubuntu-mate-{ver}-desktop-amd64.iso", "Desktop"),
    "ubuntu-budgie":  ("ubuntu-budgie",  "ubuntu-budgie-{ver}-desktop-amd64.iso", "Desktop"),
    "ubuntustudio":   ("ubuntustudio",   "ubuntustudio-{ver}-dvd-amd64.iso",    "DVD"),
}


class UbuntuFlavorsChecker(BaseChecker):
    BASE = "https://cdimage.ubuntu.com"

    def _flavor_cfg(self):
        key = self.variant or "kubuntu"
        return _FLAVOR_MAP.get(key, _FLAVOR_MAP["kubuntu"])

    def _fetch_versions(self) -> list[str]:
        slug, _, _ = self._flavor_cfg()
        url = f"{self.BASE}/{slug}/releases/"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            raw = re.findall(r'href="(\d+\.\d+(?:\.\d+)?)/"', resp.text)
            from packaging.version import Version
            unique = list(dict.fromkeys(raw))
            unique.sort(key=lambda v: Version(v), reverse=True)
            return unique
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, version: str) -> Optional[VersionInfo]:
        slug, iso_tpl, variant_label = self._flavor_cfg()
        filename = iso_tpl.format(ver=version)
        url = f"{self.BASE}/{slug}/releases/{version}/release/{filename}"
        minor = version.split(".")[1] if "." in version else "0"
        is_lts = minor == "04"
        try:
            r = requests.head(url, timeout=8, allow_redirects=True)
            if r.status_code in (200, 302):
                lbl = variant_label + (" LTS" if is_lts else "")
                sums_url = f"{self.BASE}/{slug}/releases/{version}/release/SHA256SUMS"
                checksum = fetch_sha256sums(sums_url, filename)
                return VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://wiki.ubuntu.com/Releases",
                    variant_label=lbl,
                    stable=is_lts,
                )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self._fetch_versions()
        # Prioritizes LTS versions (xx.04)
        lts = [v for v in versions if len(v.split(".")) >= 2 and v.split(".")[1] == "04"]
        for v in lts + [v for v in versions if v not in lts]:
            info = self._make_version_info(v)
            if info and info.stable:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        for v in self._fetch_versions():
            info = self._make_version_info(v)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"(?:kubuntu|xubuntu|lubuntu|ubuntu-mate|ubuntu-budgie|ubuntustudio)-(\d+\.\d+(?:\.\d+)?)-",
                      filename, re.IGNORECASE)
        return m.group(1) if m else None

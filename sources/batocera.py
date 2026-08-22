"""
Batocera — Retrogaming OS.
Source: https://mirrors.o2switch.fr/batocera/x86_64/stable/last/

updates.batocera.org (used previously) is an inconsistent front end: it
correctly redirects to this mirror for the image itself but returns 404 for
its .md5 sidecar — so the mirror is queried directly, whose listing always
gives the current build's name.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_MIRROR_URL = "https://mirrors.o2switch.fr/batocera/x86_64/stable/last/"


def _fetch_bare_md5(url: str) -> Optional[str]:
    """Batocera's .md5 sidecar contains only the checksum, without a
    filename — not the usual GNU coreutils format."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None
    m = re.match(r"^([0-9a-fA-F]{32})\s*$", resp.text.strip())
    return m.group(1).lower() if m else None


class BatoceraChecker(BaseChecker):
    MIRROR_URL = _MIRROR_URL

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.MIRROR_URL, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            m = re.search(r'href="(batocera-x86_64-([\d.]+-\d+)\.img\.gz)"', resp.text)
            if not m:
                return []
            filename, version = m.group(1), m.group(2)
            checksum = _fetch_bare_md5(self.MIRROR_URL + filename + ".md5")
            return [VersionInfo(
                version=version,
                download_url=self.MIRROR_URL + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="md5",
                variant_label="x86_64",
            )]
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"batocera-x86_64-([\d.]+-\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

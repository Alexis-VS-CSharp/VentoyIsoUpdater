"""
Version checker for Clonezilla Live.
Download: SourceForge project clonezilla/files/clonezilla_live_stable/
Version + checksum: https://clonezilla.org/downloads/stable/data/CHECKSUMS.TXT

This official file (not on SourceForge) already contains the exact name of
the current ISO file in its SHA256SUMS section — the version and checksum
are extracted in a single call, without ever needing to list the
SourceForge directory (which sometimes blocks automated requests).
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_SF_BASE = "https://sourceforge.net/projects/clonezilla/files/clonezilla_live_stable/"
_CHECKSUMS_URL = "https://clonezilla.org/downloads/stable/data/CHECKSUMS.TXT"


class ClonezillaChecker(BaseChecker):
    SF_BASE = _SF_BASE
    CHECKSUMS_URL = _CHECKSUMS_URL

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.CHECKSUMS_URL, timeout=10)
            resp.raise_for_status()
            # Isolates the SHA256SUMS section to avoid capturing the MD5/SHA1
            # one (same filenames, checksums of different lengths)
            section = resp.text.split("SHA256SUMS:")[-1]
            m = re.search(
                r"([0-9a-fA-F]{64})\s+(clonezilla-live-([\d.]+-\d+)-amd64\.iso)",
                section
            )
            if not m:
                return []
            checksum, filename, version = m.group(1), m.group(2), m.group(3)
            dl_url = f"{self.SF_BASE}{version}/{filename}/download"
            return [VersionInfo(
                version=version,
                download_url=dl_url,
                filename=filename,
                checksum=checksum.lower(),
                checksum_type="sha256",
                variant_label="amd64",
            )]
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"clonezilla-live-([\d.]+-\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

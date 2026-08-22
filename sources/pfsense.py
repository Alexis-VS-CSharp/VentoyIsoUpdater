"""
Version checker for pfSense CE.
Source: https://atxfiles.netgate.com/mirror/downloads/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger


class PfSenseChecker(BaseChecker):
    MIRROR_URL = "https://atxfiles.netgate.com/mirror/downloads/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.MIRROR_URL, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            matches = re.findall(
                r"(pfSense-CE-([\d.]+)-RELEASE-amd64\.iso(?:\.gz)?)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_bsd_sha256(self.MIRROR_URL + filename + ".sha256", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.MIRROR_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    variant_label="CE amd64",
                ))
            from packaging.version import Version
            results.sort(key=lambda x: Version(x.version), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"pfSense-CE-([\d.]+)-RELEASE", filename, re.IGNORECASE)
        return m.group(1) if m else None

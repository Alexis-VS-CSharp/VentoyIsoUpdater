"""
Version checker for DragonFlyBSD.
Source: https://mirror-master.dragonflybsd.org/iso-images/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_hashsum
from core.logger import logger


class DragonFlyBSDChecker(BaseChecker):
    BASE_URL = "https://mirror-master.dragonflybsd.org/iso-images/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r"(dfly-x86_64-([\d.]+)_REL\.iso)",
                resp.text
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                checksum = fetch_bsd_hashsum(self.BASE_URL + "md5.txt", filename, algo="MD5", hex_len=32)
                results.append(VersionInfo(
                    version=version,
                    download_url=self.BASE_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="md5",
                    variant_label="x86_64",
                ))
            from packaging.version import Version
            results.sort(key=lambda x: Version(x.version), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"dfly[^-]*-([\d.]+)_REL", filename, re.IGNORECASE)
        return m.group(1) if m else None

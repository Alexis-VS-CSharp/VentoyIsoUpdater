"""
Version checker for Zentyal.
Source: SourceForge project zentyal/files/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


def _fetch_md5(url: str, filename: str) -> Optional[str]:
    """Fetches an MD5 checksum from a SourceForge '<file>.md5' sidecar."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception:
        return None
    m = re.search(r"([0-9a-fA-F]{32})\s+\*?" + re.escape(filename), resp.text)
    return m.group(1).lower() if m else None


class ZentyalChecker(BaseChecker):
    SF_URL = "https://sourceforge.net/projects/zentyal/files/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.SF_URL,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            matches = re.findall(
                r"(zentyal-([\d.]+)-[^\"'\s<>]+\.iso)",
                resp.text, re.IGNORECASE
            )
            seen = set()
            results = []
            for filename, version in matches:
                if filename in seen:
                    continue
                seen.add(filename)
                dl_url = f"{self.SF_URL}{filename}/download"
                checksum = _fetch_md5(f"{self.SF_URL}{filename}.md5/download", filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=dl_url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="md5",
                    variant_label="Development",
                ))
            from packaging.version import Version
            results.sort(key=lambda x: Version(x.version), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"zentyal-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

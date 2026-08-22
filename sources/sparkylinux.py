"""
Version checker for SparkyLinux.
Source: https://sparkylinux.org/download/stable/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


def _fetch_archive_org_md5(url: str, filename: str) -> Optional[str]:
    """
    If `url` points to archive.org, queries the item's metadata API
    (which systematically gives an md5/sha1 per file) to retrieve
    `filename`'s checksum. Returns None for any other host.
    """
    m = re.match(r"https?://archive\.org/download/([^/]+)/", url)
    if not m:
        return None
    item = m.group(1)
    try:
        resp = requests.get(f"https://archive.org/metadata/{item}", timeout=10)
        resp.raise_for_status()
        for f in resp.json().get("files", []):
            if f.get("name") == filename:
                return f.get("md5")
    except Exception:
        pass
    return None


class SparkyLinuxChecker(BaseChecker):
    DOWNLOAD_URL = "https://sparkylinux.org/download/stable/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.DOWNLOAD_URL, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            matches = re.findall(
                r'href="([^"]+sparkylinux-([\d.]+)-x86_64-[a-z]+\.iso)"',
                resp.text, re.IGNORECASE
            )
            seen = set()
            results = []
            for url, version in matches:
                if url in seen:
                    continue
                seen.add(url)
                filename = url.split("/")[-1]
                checksum = _fetch_archive_org_md5(url, filename)
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="md5" if checksum else None,
                    variant_label="x86_64",
                ))
            from packaging.version import Version
            results.sort(key=lambda x: Version(x.version), reverse=True)
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"sparkylinux-([\d.]+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

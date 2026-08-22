"""
Version checker for antiX Linux.
Source: https://antixlinux.com/download/ — the official page gives the
current version, SourceForge links, and SHA256/MD5 checksums in plain
text (no need to reach the SourceForge sidecars for that).
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_DOWNLOAD_PAGE = "https://antixlinux.com/download/"
_SF_BASE = "https://sourceforge.net/projects/antix-linux/files/Final/"


class AntiXChecker(BaseChecker):
    DOWNLOAD_PAGE = _DOWNLOAD_PAGE

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(
                self.DOWNLOAD_PAGE, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
            # The "sha256:" block lists "<checksum> <file>" for each variant —
            # the version comes from the filename itself: a page-wide search
            # for "antiX-\d+" would also catch unrelated numbers
            # (e.g. "100%" elsewhere in the text).
            sha_block_m = re.search(r"sha256:</p>\s*<p>(.*?)</p>", resp.text, re.DOTALL)
            if not sha_block_m:
                return []
            pairs = re.findall(
                r"([0-9a-fA-F]{64})\s+(antiX-(\d+)_(?:x64|386)-(?:full|core)\.iso)",
                sha_block_m.group(1)
            )
            results = []
            for checksum, filename, version in pairs:
                if "386" in filename:
                    continue  # this project only handles amd64
                dl_url = f"{_SF_BASE}antiX-{version}/{filename}/download"
                suffix = "full" if "full" in filename else "core"
                results.append(VersionInfo(
                    version=version,
                    download_url=dl_url,
                    filename=filename,
                    checksum=checksum.lower(),
                    checksum_type="sha256",
                    variant_label=f"x64-{suffix}",
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"antiX-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

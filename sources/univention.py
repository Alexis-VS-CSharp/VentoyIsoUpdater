"""
Version checker for Univention UCS.
Source: https://updates.software-univention.de/download/ucs-cds/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class UniventionChecker(BaseChecker):
    BASE_URL = "https://updates.software-univention.de/download/ucs-cds/"

    def _fetch_versions(self) -> list[tuple[str, str]]:
        """Returns a list of (folder, version_label)."""
        try:
            resp = requests.get(self.BASE_URL, timeout=10)
            resp.raise_for_status()
            # Folders: ucs5.2-5/, ucs5.2-4/, ucs5.0-8/, etc.
            folders = re.findall(r'href="(ucs([\d.]+(?:-\d+)?))/"', resp.text)
            # Sorts by descending version
            def sort_key(item):
                folder, ver = item
                # e.g. ucs5.2-5 -> (5, 2, 5)
                parts = re.findall(r'\d+', folder)
                return tuple(int(p) for p in parts)
            folders_sorted = sorted(set(folders), key=sort_key, reverse=True)
            return folders_sorted
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _make_version_info(self, folder: str, ver_label: str) -> Optional[VersionInfo]:
        dir_url = f"{self.BASE_URL}{folder}/"
        try:
            resp = requests.get(dir_url, timeout=10)
            resp.raise_for_status()
            # Looks for UCS_5.2-5-amd64.iso or similar
            isos = re.findall(
                r'(UCS_([\d.]+(?:-\d+)?)-amd64\.iso)',
                resp.text, re.IGNORECASE
            )
            for filename, version in isos[:1]:
                checksum = fetch_sha256sums(dir_url + filename + ".sha256", filename)
                return VersionInfo(
                    version=version,
                    download_url=dir_url + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://docs.software-univention.de/",
                    variant_label="UCS",
                )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        # Fallback: direct HEAD
        m = re.search(r'ucs([\d.]+(?:-\d+)?)', folder)
        if m:
            ver = m.group(1)
            filename = f"UCS_{ver}-amd64.iso"
            url = dir_url + filename
            try:
                r = requests.head(url, timeout=8, allow_redirects=True)
                if r.status_code in (200, 302):
                    return VersionInfo(
                        version=ver,
                        download_url=url,
                        filename=filename,
                        release_notes_url="https://docs.software-univention.de/",
                        variant_label="UCS",
                    )
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                pass
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        for folder, ver in self._fetch_versions():
            info = self._make_version_info(folder, ver)
            if info:
                return info
        return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        for folder, ver in self._fetch_versions():
            info = self._make_version_info(folder, ver)
            if info:
                results.append(info)
        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"(?:UCS|univention)[^\d]*([\d.]+(?:-\d+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None

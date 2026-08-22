"""
Version checker for Kali Linux.
Source: https://cdimage.kali.org/
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class KaliChecker(BaseChecker):
    CURRENT_URL = "https://cdimage.kali.org/current/"
    ARCHIVE_URL = "https://cdimage.kali.org/kali-images/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        try:
            resp = requests.get(self.CURRENT_URL, timeout=10)
            resp.raise_for_status()
            matches = re.findall(
                r'(kali-linux-(\d{4}\.\d+)-installer-amd64\.iso)', resp.text
            )
            if not matches:
                return None
            filename, version = max(matches, key=lambda x: x[1])
            checksum = fetch_sha256sums(self.CURRENT_URL + "SHA256SUMS", filename)
            return VersionInfo(
                version=version,
                download_url=self.CURRENT_URL + filename,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url="https://www.kali.org/news/",
                variant_label="Installer",
            )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        try:
            resp = requests.get(self.ARCHIVE_URL, timeout=10)
            resp.raise_for_status()
            release_dirs = re.findall(r'href="(kali-\d{4}\.\d+)/?"', resp.text)
            release_dirs = sorted(set(release_dirs), reverse=True)[:10]

            for rdir in release_dirs:
                url = f"{self.ARCHIVE_URL}{rdir}/"
                try:
                    r2 = requests.get(url, timeout=8)
                    r2.raise_for_status()
                    matches = re.findall(
                        r'(kali-linux-(\d{4}\.\d+)-installer-amd64\.iso)', r2.text
                    )
                    for filename, version in matches:
                        checksum = fetch_sha256sums(url + "SHA256SUMS", filename)
                        results.append(VersionInfo(
                            version=version,
                            download_url=url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url="https://www.kali.org/news/",
                            variant_label="Installer",
                        ))
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            latest = self.get_latest_version()
            if latest:
                results.append(latest)

        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"kali-linux-(\d{4}\.\d+)-", filename, re.IGNORECASE)
        return m.group(1) if m else None

"""
Version checker for Arch Linux (rolling release).
Sources: official pkgbuild.com and rackspace.com mirrors
"""

import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger


class ArchChecker(BaseChecker):
    # Reliable mirrors in order of preference (all HTTP/HTTPS)
    MIRRORS = [
        "https://geo.mirror.pkgbuild.com/iso/",
        "https://fastly.mirror.pkgbuild.com/iso/",
        "https://mirror.rackspace.com/archlinux/iso/",
    ]

    def _get(self, path: str, **kwargs) -> requests.Response:
        """
        Tries each mirror in order and returns the first 200 response.
        `path` is relative to the mirror's root (e.g. 'latest/' or '2026.03.01/').
        """
        last_exc = None
        for base in self.MIRRORS:
            try:
                resp = requests.get(base + path, timeout=10, **kwargs)
                resp.raise_for_status()
                return resp
            except Exception as exc:
                last_exc = exc
                continue
        raise last_exc

    def get_latest_version(self) -> Optional[VersionInfo]:
        try:
            resp = self._get("latest/")
            m = re.search(r'(archlinux-(\d{4}\.\d{2}\.\d{2})-x86_64\.iso)', resp.text)
            if not m:
                return None
            filename, version = m.group(1), m.group(2)
            # Uses the mirror that responded as the download URL base
            download_url = resp.url.rsplit("/", 1)[0] + "/" + filename if resp.url.endswith(filename) else resp.url.rstrip("/") + "/" + filename
            # Simplification: cleanly rebuilds the URL from the effective URL
            base_used = next(
                (b for b in self.MIRRORS if resp.url.startswith(b)),
                resp.url.rsplit("latest/", 1)[0] + "iso/"
            )
            download_url = base_used + "latest/" + filename
            checksum = fetch_sha256sums(base_used + "latest/sha256sums.txt", filename)
            return VersionInfo(
                version=version,
                download_url=download_url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url="https://archlinux.org/download/",
                variant_label="Rolling",
                stable=False,
            )
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        try:
            resp = self._get("")
            dates = re.findall(r'href="(\d{4}\.\d{2}\.\d{2})/?"', resp.text)
            dates = sorted(set(dates), reverse=True)[:12]  # last 12 releases

            # Determines which mirror responded, for the archive
            base_used = next(
                (b for b in self.MIRRORS if resp.url.startswith(b)),
                self.MIRRORS[0]
            )

            for date in dates:
                url = f"{base_used}{date}/"
                try:
                    r2 = requests.get(url, timeout=8)
                    r2.raise_for_status()
                    m = re.search(r'(archlinux-(\d{4}\.\d{2}\.\d{2})-x86_64\.iso)', r2.text)
                    if m:
                        filename, version = m.group(1), m.group(2)
                        checksum = fetch_sha256sums(url + "sha256sums.txt", filename)
                        results.append(VersionInfo(
                            version=version,
                            download_url=url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url="https://archlinux.org/download/",
                            variant_label="Rolling",
                            stable=False,
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
        m = re.search(r"archlinux-(\d{4}\.\d{2}\.\d{2})-", filename, re.IGNORECASE)
        return m.group(1) if m else None

    def is_outdated(self, local_version: str, latest_version: str) -> bool:
        return local_version < latest_version

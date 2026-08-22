"""
Pop!_OS — System76.
Source: https://api.pop-os.org/builds/{version}/{channel}?arch={arch}
The API returns: url, sha_sum, size, build, version, channel.
"""

import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


class PopOSChecker(BaseChecker):
    # Supported LTS versions, most recent first
    VERSIONS = ["24.04", "22.04"]

    # Mapping of variant (user-facing parameter) -> API channel
    CHANNEL_MAP = {
        "intel": "generic",
        "amd":   "generic",
        "generic": "generic",
        "nvidia": "nvidia",
    }

    API_BASE = "https://api.pop-os.org/builds"

    def _fetch_release(self, version: str, channel: str, arch: str = "amd64") -> Optional[dict]:
        """
        Calls the System76 API and returns the JSON dict, or None on error.
        """
        url = f"{self.API_BASE}/{version}/{channel}?arch={arch}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if "errors" in data:
                return None
            return data
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = (self.variant or "intel").lower()
        channel = self.CHANNEL_MAP.get(variant, "generic")
        results = []

        for version in self.VERSIONS:
            data = self._fetch_release(version, channel)
            if data is None:
                continue
            iso_url = data.get("url", "")
            filename = iso_url.rsplit("/", 1)[-1] if iso_url else ""
            sha_sum = data.get("sha_sum") or None
            size_bytes = data.get("size")
            size_hint = f"{size_bytes / 1_073_741_824:.1f} GB" if size_bytes else None
            variant_label = f"{'NVIDIA' if channel == 'nvidia' else 'Intel/AMD'} {version}"

            results.append(VersionInfo(
                version=version,
                download_url=iso_url,
                filename=filename,
                checksum=sha_sum,
                checksum_type="sha256",
                release_notes_url="https://system76.com/pop",
                variant_label=variant_label,
                size_hint=size_hint,
            ))

        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        import re
        m = re.search(r"pop-os_(\d+\.\d+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

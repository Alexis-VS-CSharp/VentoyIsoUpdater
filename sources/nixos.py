"""
Version checker for NixOS.
Source: channels.nixos.org (resolves the exact build of the current stable
channel) + releases.nixos.org (build page: lists files AND their SHA256
checksum directly in the HTML — no separate file needed).

NixOS no longer publishes separate ISOs per desktop environment: as of
recent versions, only "graphical" (desktop, GNOME by default) and
"minimal" (no interface) are offered. This checker's "gnome"/"kde"
variants therefore both point to the "graphical" ISO.
"""

import re
import requests
from datetime import date
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


class NixOSChecker(BaseChecker):
    # variant: 'gnome'/'kde' (-> graphical), 'minimal'
    CHANNELS_URL = "https://channels.nixos.org/nixos-"
    RELEASES_URL = "https://releases.nixos.org/nixos/"

    def _candidate_channels(self, count: int = 6) -> list[str]:
        """
        Generates the most likely recent stable channel names
        (format "YY.MM", releases in May and November), most recent
        first, without depending on a "latest" entry point, which
        doesn't exist for NixOS.
        """
        today = date.today()
        year, month = today.year, today.month
        if month < 5:
            year, month = year - 1, 11
        elif month < 11:
            year, month = year, 5
        else:
            year, month = year, 11

        out = []
        for _ in range(count):
            out.append(f"{year % 100:02d}.{month:02d}")
            month = 5 if month == 11 else 11
            if month == 11:
                year -= 1
        return out

    def _resolve_build(self, channel: str) -> Optional[str]:
        """Resolves 'nixos-25.05' to the exact URL of the current build page."""
        try:
            r = requests.head(self.CHANNELS_URL + channel, timeout=10, allow_redirects=True)
            if r.status_code == 200 and "/nixos/" in r.url:
                return r.url
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
        return None

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "gnome"
        prefix = "nixos-minimal-" if variant == "minimal" else "nixos-graphical-"
        label = "Minimal" if variant == "minimal" else "Graphical"

        for channel in self._candidate_channels():
            build_url = self._resolve_build(channel)
            if not build_url:
                continue
            try:
                resp = requests.get(build_url, timeout=10)
                resp.raise_for_status()
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                continue

            # The build page lists "<a href='.../<file>.iso'>...</a></td>
            # <td>size</td><td><tt><sha256 checksum></tt></td>" for each
            # file — the name AND checksum are captured in a single pass.
            pattern = re.compile(
                r"href='([^']*/" + re.escape(prefix) + r"[\w.-]+-x86_64-linux\.iso)'"
                r"[^<]*</a></td><td[^>]*>\d+</td><td><tt>([0-9a-f]{64})</tt>"
            )
            m = pattern.search(resp.text)
            if not m:
                continue
            path, checksum = m.group(1), m.group(2)
            filename = path.rsplit("/", 1)[-1]
            v_m = re.search(r"-((?:\d+\.\d+)(?:pre\d+)?\.[\w]+\.[0-9a-f]+)-x86_64", filename)
            version = v_m.group(1) if v_m else channel
            return [VersionInfo(
                version=version,
                download_url="https://releases.nixos.org" + path,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256",
                release_notes_url="https://nixos.org/blog/announcements/",
                variant_label=label,
            )]
        return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"nixos-(?:graphical|minimal)-([\w.]+)-x86_64", filename, re.IGNORECASE)
        return m.group(1) if m else None

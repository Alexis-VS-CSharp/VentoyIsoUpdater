"""
openSUSE Leap and Tumbleweed. Source: download.opensuse.org (see
https://en.opensuse.org/SDB:Download_help#Checksums).

The mirrors.edge.kernel.org mirror used previously does list the
"Current.iso" files in its index, but those are dead links (404) on that
specific mirror — for both the ISO and its ".sha256". download.opensuse.org
is the official entry point: it redirects (302) to a mirror that actually
serves the file, for both the ISO and the checksum.

The <iso>.sha256 file fetched after redirection references the real build
name (e.g. "...-Build710.3-Media.iso"), not "Current.iso" — so the single
SHA256 checksum it contains is extracted rather than matching an exact
filename.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


def _fetch_current_sha256(sha256_url: str) -> Optional[str]:
    """
    Fetches the SHA256 checksum from a '<iso>.sha256' sidecar pointing to
    "Current": the file only contains a single relevant checksum, under its
    real build name (e.g. '...-Build710.3-Media.iso'), so the first one
    found is used rather than matching an exact filename.
    """
    try:
        resp = requests.get(sha256_url, timeout=10)
        resp.raise_for_status()
    except Exception as _exc:
        logger.debug("%s: failed, ignored: %s", __name__, _exc)
        return None
    m = re.search(r"^([0-9a-fA-F]{64})\s+\*?\S+\.iso\s*$", resp.text, re.MULTILINE)
    return m.group(1).lower() if m else None


class OpenSUSEChecker(BaseChecker):
    # variant: 'leap' or 'tumbleweed'
    LEAP_URL = "https://download.opensuse.org/distribution/leap/"
    TW_URL   = "https://download.opensuse.org/tumbleweed/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        variant = self.variant or "leap"
        if variant == "tumbleweed":
            return self._fetch_tumbleweed()
        return self._fetch_leap()

    def _fetch_leap(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.LEAP_URL, timeout=10)
            resp.raise_for_status()
            versions = re.findall(r'href="(?:\./)?(\d+\.\d+)/"', resp.text)
            from packaging.version import Version as PV
            # Excludes the 42.x branch (old, < 2018) — openSUSE moved to 15.x
            unique = [v for v in dict.fromkeys(versions) if not v.startswith("42.")]
            unique.sort(key=lambda v: PV(v), reverse=True)

            results = []
            for ver in unique[:6]:
                iso_url = f"{self.LEAP_URL}{ver}/iso/"
                try:
                    r2 = requests.get(iso_url, timeout=8)
                    r2.raise_for_status()
                    isos = re.findall(
                        rf'(openSUSE-Leap-{re.escape(ver)}-DVD-x86_64-[^"]+\.iso)',
                        r2.text
                    )
                    if not isos:
                        isos = re.findall(r'(openSUSE-Leap-[\d.]+-[^"]+\.iso)', r2.text)
                    for filename in isos[:1]:
                        checksum = _fetch_current_sha256(iso_url + filename + ".sha256")
                        results.append(VersionInfo(
                            version=ver,
                            download_url=iso_url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url=f"https://doc.opensuse.org/release-notes/x86_64/openSUSE/Leap/{ver}/",
                            variant_label=f"Leap {ver}",
                            stable=True,
                        ))
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def _fetch_tumbleweed(self) -> list[VersionInfo]:
        try:
            resp = requests.get(self.TW_URL, timeout=10)
            resp.raise_for_status()
            isos = re.findall(
                r'(openSUSE-Tumbleweed-DVD-x86_64-[^"]+\.iso)',
                resp.text
            )
            results = []
            for filename in isos[:3]:
                m = re.search(r'Tumbleweed-DVD-x86_64-(\d+)', filename)
                version = m.group(1) if m else "latest"
                checksum = _fetch_current_sha256(self.TW_URL + filename + ".sha256")
                results.append(VersionInfo(
                    version=version,
                    download_url=self.TW_URL + filename,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha256",
                    release_notes_url="https://opensuse.github.io/openSUSE-release-tools/tumbleweed-review.html",
                    variant_label="Tumbleweed (Rolling)",
                    stable=False,
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"openSUSE-(?:Leap|Tumbleweed)[^-]*-([\d.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

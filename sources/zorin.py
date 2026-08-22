"""Zorin OS. Source: official download pages (zorinos.com) — scrapes mirror list."""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha256sums
from core.logger import logger

# Zorin's official download pages embed a list of mirror URLs directly in the HTML.
# Each page corresponds to a single edition (Core, Education) and links to the
# current/latest ISO only — there is no archive. We parse the first ISO URL to
# extract the filename, then use the kernel.org mirror as the canonical download URL.

DOWNLOAD_PAGES = {
    "core":      "https://zorin.com/os/download/18/core/",
    "education": "https://zorin.com/os/download/18/education/",
}

# Primary mirror used as canonical download_url
PRIMARY_MIRROR = "https://mirrors.edge.kernel.org/zorinos-isos/18/{filename}"


class ZorinChecker(BaseChecker):
    """Checker for Zorin OS Core and Education editions."""

    def get_latest_version(self) -> Optional[VersionInfo]:
        variant = (self.variant or "core").lower()
        page_url = DOWNLOAD_PAGES.get(variant)
        if not page_url:
            return None

        try:
            resp = requests.get(
                page_url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            resp.raise_for_status()
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return None

        # The page HTML contains mirror hrefs of the form:
        #   https://<mirror>/.../<version>/<filename>.iso
        # All mirrors point to the same filename, so we just need the first match.
        iso_match = re.search(
            r'href="(https?://[^"]+/(Zorin-OS-[^"/]+\.iso))"',
            resp.text,
        )
        if not iso_match:
            return None

        filename = iso_match.group(2)

        # Extract version: "18" from "Zorin-OS-18-Core-64-bit-r3.iso"
        # Also capture revision suffix (e.g. "-r3") for a rich version string.
        ver_match = re.search(r"Zorin-OS-(\d+(?:\.\d+)?)((?:-r\d+)?)-", filename)
        if not ver_match:
            return None

        base_version = ver_match.group(1)          # "18"
        revision     = ver_match.group(2).lstrip("-")  # "r3" or ""
        version      = f"{base_version}.{revision}" if revision else base_version

        download_url = PRIMARY_MIRROR.format(filename=filename)
        # Not exposed on the download page itself, but the kernel.org
        # mirror serves a SHA256SUMS.txt covering every file.
        sums_url = download_url.rsplit("/", 1)[0] + "/SHA256SUMS.txt"
        checksum = fetch_sha256sums(sums_url, filename)

        return VersionInfo(
            version=version,
            download_url=download_url,
            filename=filename,
            checksum=checksum,
            checksum_type="sha256" if checksum else None,
            release_notes_url=page_url,
            variant_label=variant.capitalize(),
            stable=True,
        )

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Zorin-OS-(\d+(?:\.\d+)?)((?:-r\d+)?)-", filename, re.IGNORECASE)
        if not m:
            return None
        base     = m.group(1)
        revision = m.group(2).lstrip("-")
        return f"{base}.{revision}" if revision else base

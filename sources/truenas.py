"""TrueNAS SCALE.
Source: https://www.truenas.com/download/
The ISO links are embedded directly in the download page's HTML.
Real URLs: https://download.sys.truenas.net/TrueNAS-SCALE-{CodeName}/{ver}/TrueNAS-SCALE-{ver}.iso
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger

_DL_PAGE = "https://www.truenas.com/download/"
# Pattern extracted from the HTML: the ISO links are hardcoded in the page
_ISO_RE = re.compile(
    r'https://download\.sys\.truenas\.net/'
    r'(TrueNAS-SCALE-(\w+))/'       # group 1 = codename folder, group 2 = codename alone
    r'([\d.]+)/'                     # group 3 = version
    r'(TrueNAS-SCALE-[\d.]+\.iso)',  # group 4 = filename
    re.IGNORECASE,
)


class TrueNASChecker(BaseChecker):

    def _fetch_versions(self) -> list[VersionInfo]:
        try:
            resp = requests.get(_DL_PAGE, timeout=15)
            resp.raise_for_status()
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

        seen: set[str] = set()
        results: list[VersionInfo] = []

        for m in _ISO_RE.finditer(resp.text):
            codename_dir = m.group(1)   # e.g. TrueNAS-SCALE-Fangtooth
            codename     = m.group(2)   # e.g. Fangtooth
            version      = m.group(3)   # e.g. 25.04.2.6
            filename     = m.group(4)   # e.g. TrueNAS-SCALE-25.04.2.6.iso
            url          = m.group(0)

            if filename in seen:
                continue
            seen.add(filename)

            # Stable if month == 04 (TrueNAS convention: .04 = production, .10 = beta)
            parts = version.split(".")
            month = parts[1] if len(parts) >= 2 else "0"
            stable = (month == "04")

            # Tries to fetch the sha256
            sha_url = url + ".sha256"
            checksum = None
            try:
                r2 = requests.get(sha_url, timeout=8)
                if r2.ok:
                    # Line of the form "abc123...  TrueNAS-SCALE-25.04.2.6.iso"
                    checksum = r2.text.split()[0] if r2.text.strip() else None
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                pass

            results.append(VersionInfo(
                version=version,
                download_url=url,
                filename=filename,
                checksum=checksum,
                checksum_type="sha256" if checksum else None,
                release_notes_url="https://www.truenas.com/docs/",
                variant_label=f"SCALE {codename}",
                stable=stable,
            ))

        # Sorts by descending version
        try:
            from packaging.version import Version as PV, InvalidVersion
            results.sort(key=lambda v: _pv(v.version), reverse=True)
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        return results

    def get_latest_version(self) -> Optional[VersionInfo]:
        all_v = self._fetch_versions()
        # Prefers the latest stable version
        stable = [v for v in all_v if v.stable]
        return (stable or all_v or [None])[0]

    def get_all_versions(self) -> list[VersionInfo]:
        return self._fetch_versions()

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"TrueNAS-(?:CORE|SCALE)[_-]([\d.]+(?:U[\d.]+)?)", filename, re.IGNORECASE)
        return m.group(1) if m else None


def _pv(v: str):
    from packaging.version import Version as PV, InvalidVersion
    try:
        return PV(v)
    except InvalidVersion:
        return PV("0")

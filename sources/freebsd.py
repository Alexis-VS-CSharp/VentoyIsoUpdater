"""FreeBSD. Source: download.freebsd.org

Publishes a real, generic ISO for both amd64 and arm64. FreeBSD's own path
scheme doubles the arch name for arm64 both in the URL
(.../releases/arm64/aarch64/...) and in filenames themselves
(FreeBSD-15.1-RELEASE-arm64-aarch64-disc1.iso) — amd64 only ever appears
once in each. Older arm64 releases only shipped a generic "bootonly"
image; disc1/dvd1 have since been added too, but the bootonly fallback
stays in case a future release drops them again.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_bsd_sha256
from core.logger import logger

# (URL path segment, tag used in filenames/checksum names — arm64 repeats
# the family before the ABI in both the path AND the filename, e.g.
# ".../releases/arm64/aarch64/..." and "FreeBSD-15.1-RELEASE-arm64-aarch64-disc1.iso";
# amd64 only ever appears once in each)
_ARCH_PATH = {"amd64": ("amd64", "amd64"), "arm64": ("arm64", "arm64-aarch64")}


class FreeBSDChecker(BaseChecker):

    def _releases_url(self) -> str:
        # New path since FreeBSD 14+
        family, tag = _ARCH_PATH.get(self.arch, _ARCH_PATH["amd64"])
        abi = tag.rsplit("-", 1)[-1]
        return f"https://download.freebsd.org/releases/{family}/{abi}/ISO-IMAGES/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        family, tag = _ARCH_PATH.get(self.arch, _ARCH_PATH["amd64"])
        releases_url = self._releases_url()
        try:
            resp = requests.get(releases_url, timeout=10)
            resp.raise_for_status()

            # Version folders: 14.0/, 15.0/, etc.
            # Leading \d+: excludes the "parent folder" link (href="../")
            # which [\d.]+ would also capture ('..' is made only of dots).
            dirs = re.findall(r'href="(\d+(?:\.\d+)*)/?"', resp.text)
            from packaging.version import Version as PV
            unique = list(dict.fromkeys(dirs))
            unique.sort(key=lambda v: PV(v), reverse=True)

            results = []
            for ver in unique[:5]:
                iso_url = f"{releases_url}{ver}/"
                try:
                    r2 = requests.get(iso_url, timeout=8)
                    r2.raise_for_status()
                    # Looks for disc1.iso or dvd1.iso first
                    isos = re.findall(
                        rf'(FreeBSD-[\d.]+-RELEASE-{tag}-(?:disc1|dvd1)\.iso)',
                        r2.text
                    )
                    variant_label = "disc1"
                    if not isos:
                        # Board-specific bootonly images carry a suffix
                        # (e.g. "-RPI", "-PINE64") — only the bare one
                        # (no suffix) is the generic, Ventoy-bootable one.
                        isos = re.findall(
                            rf'(FreeBSD-[\d.]+-RELEASE-{tag}-(?:memstick|bootonly)\.iso)',
                            r2.text
                        )
                        variant_label = "bootonly"
                    for filename in isos[:1]:
                        m = re.search(r'FreeBSD-([\d.]+-RELEASE)', filename)
                        rel = m.group(1) if m else ver
                        sums_url = f"{iso_url}CHECKSUM.SHA256-FreeBSD-{rel}-{tag}"
                        checksum = fetch_bsd_sha256(sums_url, filename)
                        results.append(VersionInfo(
                            version=rel,
                            download_url=iso_url + filename,
                            filename=filename,
                            checksum=checksum,
                            checksum_type="sha256",
                            release_notes_url="https://www.freebsd.org/releases/",
                            variant_label=variant_label,
                            arch=self.arch,
                        ))
                except Exception as _exc:
                    logger.debug("%s: failed, ignored: %s", __name__, _exc)
                    continue
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"FreeBSD-([\d.]+-RELEASE)", filename, re.IGNORECASE)
        return m.group(1) if m else None

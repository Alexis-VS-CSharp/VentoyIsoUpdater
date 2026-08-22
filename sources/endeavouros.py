"""EndeavourOS — Arch-based distro. Source: endeavouros.com/latest-release/"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from sources._checksum import fetch_sha512sums
from core.logger import logger


class EndeavourOSChecker(BaseChecker):
    RELEASE_PAGE = "https://endeavouros.com/latest-release/"
    MIRROR_BASE  = "https://mirror.rznet.fr/endeavouros/iso/"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        results = []
        try:
            # Scrapes the release page to find direct ISO URLs
            resp = requests.get(self.RELEASE_PAGE, timeout=10)
            resp.raise_for_status()
            isos = re.findall(
                r'https://[^\s"]+EndeavourOS[^\s"]+\.iso',
                resp.text
            )
            seen = set()
            for url in isos:
                filename = url.split("/")[-1]
                if filename in seen:
                    continue
                seen.add(filename)
                m = re.search(r'EndeavourOS[_-]?(?:\w+[_-])*(\d{4}\.\d{2}\.\d{2})', filename)
                version = m.group(1) if m else "latest"
                # Sidecar '<file>.sha512sum' (older releases) or
                # '.sha512' (recent ones) — tried against the resolved mirror.
                base_url = url.rsplit("/", 1)[0] + "/"
                checksum = (
                    fetch_sha512sums(base_url + filename + ".sha512sum", filename)
                    or fetch_sha512sums(base_url + filename + ".sha512", filename)
                )
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    checksum=checksum,
                    checksum_type="sha512",
                    release_notes_url=self.RELEASE_PAGE,
                    variant_label="EndeavourOS",
                ))
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        if not results:
            # Fallback: direct mirror
            try:
                resp = requests.get(self.MIRROR_BASE, timeout=10)
                resp.raise_for_status()
                isos = re.findall(r'(EndeavourOS[^"]+\.iso)', resp.text)
                for filename in isos[:4]:
                    m = re.search(r'(\d{4}\.\d{2}\.\d{2})', filename)
                    version = m.group(1) if m else "latest"
                    # Sidecar '<file>.sha512sum' on older releases,
                    # '<file>.sha512' on newer ones.
                    checksum = (
                        fetch_sha512sums(self.MIRROR_BASE + filename + ".sha512sum", filename)
                        or fetch_sha512sums(self.MIRROR_BASE + filename + ".sha512", filename)
                    )
                    results.append(VersionInfo(
                        version=version,
                        download_url=self.MIRROR_BASE + filename,
                        filename=filename,
                        checksum=checksum,
                        checksum_type="sha512",
                        release_notes_url=self.RELEASE_PAGE,
                        variant_label="EndeavourOS",
                    ))
            except Exception as _exc:
                logger.debug("%s: failed, ignored: %s", __name__, _exc)
                pass

        return results

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"EndeavourOS[_-]?(?:\w+[_-])*(\d{4}\.\d{2}\.\d{2})", filename, re.IGNORECASE)
        return m.group(1) if m else None

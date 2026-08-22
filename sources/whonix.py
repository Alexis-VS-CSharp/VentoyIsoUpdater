"""
Whonix — privacy-focused OS (VM-based).
Source: Whonix/Whonix GitHub releases or the official download page.
"""
import re
import requests
from typing import Optional
from sources.base import BaseChecker, VersionInfo
from core.logger import logger


class WhonixChecker(BaseChecker):
    GITHUB_API = "https://api.github.com/repos/Whonix/Whonix/releases"
    DL_PAGE = "https://www.whonix.org/wiki/Download"

    def get_latest_version(self) -> Optional[VersionInfo]:
        versions = self.get_all_versions()
        return versions[0] if versions else None

    def get_all_versions(self) -> list[VersionInfo]:
        # Attempt 1: GitHub releases
        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            resp = requests.get(
                self.GITHUB_API, timeout=12, headers=headers,
                params={"per_page": 10}
            )
            resp.raise_for_status()
            releases = resp.json()
            results = []
            for release in releases:
                if release.get("draft"):
                    continue
                version = release.get("tag_name", "").lstrip("v")
                for asset in release.get("assets", []):
                    name = asset.get("name", "")
                    if re.search(r"Whonix[^\"]*\.(ova|iso)$", name, re.IGNORECASE):
                        results.append(VersionInfo(
                            version=version,
                            download_url=asset["browser_download_url"],
                            filename=name,
                            variant_label="VirtualBox" if name.endswith(".ova") else "ISO",
                        ))
            if results:
                return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            pass

        # Attempt 2: wiki download page
        try:
            resp = requests.get(
                self.DL_PAGE, timeout=12,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            links = re.findall(
                r'href="([^"]+Whonix[^"]*\.(ova|iso))"',
                resp.text, re.IGNORECASE
            )
            results = []
            seen = set()
            for url, ext in links:
                if url in seen:
                    continue
                seen.add(url)
                if not url.startswith("http"):
                    url = "https://www.whonix.org" + url
                filename = url.split("/")[-1].split("?")[0]
                m = re.search(r"Whonix[^-]*-[^-]+-([0-9.]+)", filename, re.IGNORECASE)
                version = m.group(1) if m else "latest"
                results.append(VersionInfo(
                    version=version,
                    download_url=url,
                    filename=filename,
                    variant_label="VirtualBox" if ext.lower() == "ova" else "ISO",
                ))
            return results
        except Exception as _exc:
            logger.debug("%s: failed, ignored: %s", __name__, _exc)
            return []

    def parse_local_version(self, filename: str) -> Optional[str]:
        m = re.search(r"Whonix[^-]*-[^-]+-([0-9.]+)", filename, re.IGNORECASE)
        return m.group(1) if m else None

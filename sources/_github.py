"""
Generic helper for fetching ISO releases from GitHub.
Used by several sources (Bazzite, EndeavourOS, ChimeraOS, Batocera, etc.)
"""

import re
import requests
from typing import Optional
from sources.base import VersionInfo
from core.logger import logger


def get_github_iso_releases(
    owner: str,
    repo: str,
    asset_pattern: str,
    variant_label: Optional[str] = None,
    max_releases: int = 10,
    skip_prereleases: bool = True,
) -> list[VersionInfo]:
    """
    Fetches releases from a GitHub repo and filters ISO assets.

    Args:
        owner: GitHub owner (e.g. 'ublue-os')
        repo: repo name (e.g. 'bazzite')
        asset_pattern: regex to filter assets (e.g. r'Bazzite-.*\\.iso$')
        variant_label: label shown in the UI
        max_releases: max number of releases to inspect
        skip_prereleases: skips pre-releases and drafts
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    try:
        resp = requests.get(url, timeout=12, headers=headers,
                            params={"per_page": max_releases})
        resp.raise_for_status()
        releases = resp.json()
    except Exception as _exc:
        logger.debug("%s: failed, ignored: %s", __name__, _exc)
        return []

    results = []
    for release in releases:
        if skip_prereleases and (release.get("prerelease") or release.get("draft")):
            continue
        version = release.get("tag_name", "").lstrip("v")
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            if re.search(asset_pattern, name, re.IGNORECASE):
                results.append(VersionInfo(
                    version=version,
                    download_url=asset["browser_download_url"],
                    filename=name,
                    variant_label=variant_label or repo,
                ))
    return results

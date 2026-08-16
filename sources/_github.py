"""
Helper générique pour récupérer des releases ISO depuis GitHub.
Utilisé par plusieurs sources (Bazzite, EndeavourOS, ChimeraOS, Batocera, etc.)
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
    Récupère les releases d'un dépôt GitHub et filtre les assets ISO.

    Args:
        owner: propriétaire GitHub (ex: 'ublue-os')
        repo: nom du dépôt (ex: 'bazzite')
        asset_pattern: regex pour filtrer les assets (ex: r'Bazzite-.*\\.iso$')
        variant_label: libellé affiché dans l'UI
        max_releases: nombre max de releases à inspecter
        skip_prereleases: ignore les pre-releases et drafts
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}

    try:
        resp = requests.get(url, timeout=12, headers=headers,
                            params={"per_page": max_releases})
        resp.raise_for_status()
        releases = resp.json()
    except Exception as _exc:
        logger.debug("%s: échec ignoré : %s", __name__, _exc)
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

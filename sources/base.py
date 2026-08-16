"""
Classe de base abstraite pour tous les vérificateurs de version de distro.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VersionInfo:
    version: str
    download_url: str
    filename: str
    checksum: Optional[str] = None
    checksum_type: Optional[str] = None  # 'sha256', 'md5', etc.
    release_notes_url: Optional[str] = None
    # Renseigné quand aucune empreinte automatique n'est disponible mais que
    # la source publie une méthode de vérification manuelle (signature
    # OpenPGP, vérificateur web, etc.) — l'UI invite alors l'utilisateur à
    # vérifier lui-même via cette page plutôt que de laisser croire à une
    # intégrité non contrôlée. Ex: Tails (uniquement une signature OpenPGP).
    manual_verify_url: Optional[str] = None
    # Infos optionnelles pour le navigateur de versions
    variant_label: Optional[str] = None   # ex: "Desktop", "Server", "Netinst"
    arch: str = "amd64"
    size_hint: Optional[str] = None       # ex: "2.5 GB" si connu
    stable: bool = True                   # False pour les versions non-LTS, rolling, beta


class BaseChecker(ABC):

    def __init__(self, variant: Optional[str] = None):
        self.variant = variant

    @abstractmethod
    def get_latest_version(self) -> Optional[VersionInfo]:
        """
        Interroge la source en ligne et retourne les infos de la dernière version.
        Retourne None en cas d'échec ou si non applicable.
        """
        pass

    def get_all_versions(self) -> list[VersionInfo]:
        """
        Retourne toutes les versions disponibles en ligne pour cette distro/variante.
        Par défaut retourne uniquement la dernière version.
        Surcharger dans les sous-classes pour lister l'historique.
        """
        latest = self.get_latest_version()
        return [latest] if latest else []

    @abstractmethod
    def parse_local_version(self, filename: str) -> Optional[str]:
        """
        Extrait la version d'un nom de fichier ISO local.
        Retourne None si le fichier n'est pas reconnu.
        """
        pass

    def is_outdated(self, local_version: str, latest_version: str) -> bool:
        """
        Compare deux chaînes de version.
        Retourne True si local_version est inférieure à latest_version.
        """
        from packaging.version import Version, InvalidVersion
        try:
            return Version(local_version) < Version(latest_version)
        except InvalidVersion:
            # Fallback : comparaison lexicographique (utile pour les dates YYYY.MM.DD)
            return local_version < latest_version

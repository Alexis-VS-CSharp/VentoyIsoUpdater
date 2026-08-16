"""
Orchestre la vérification de version pour chaque ISO détectée.
Utilise un ThreadPoolExecutor pour les checks en parallèle.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable

from core.ventoy_scanner import IsoEntry
from sources.base import VersionInfo


class UpdateStatus(Enum):
    UP_TO_DATE = "À jour"
    OUTDATED = "Mise à jour disponible"
    UNKNOWN = "Non reconnue"
    MANUAL = "Vérification manuelle"
    ERROR = "Erreur"
    CHECKING = "Vérification..."


@dataclass
class CheckResult:
    iso: IsoEntry
    status: UpdateStatus
    latest_info: Optional[VersionInfo] = None
    error_msg: Optional[str] = None


# Registre des checkers : checker_id → classe
_CHECKER_REGISTRY: dict = {}
import threading as _threading
_CHECKER_LOCK = _threading.Lock()


def _load_checkers():
    global _CHECKER_REGISTRY
    if _CHECKER_REGISTRY:
        return
    with _CHECKER_LOCK:
        if _CHECKER_REGISTRY:   # double-check après acquisition du verrou
            return
        # Tous les imports et l'update sont dans le verrou pour éviter la race condition
        from sources.ubuntu import UbuntuChecker
        from sources.debian import DebianChecker
        from sources.fedora import FedoraChecker
        from sources.linuxmint import LinuxMintChecker
        from sources.arch import ArchChecker
        from sources.kali import KaliChecker
        from sources.rocky import RockyChecker
        from sources.almalinux import AlmaLinuxChecker
        from sources.windows import WindowsChecker
        from sources.bazzite import BazziteChecker
        from sources.nobara import NobaraChecker
        from sources.chimeraos import ChimeraOSChecker
        from sources.batocera import BatoceraChecker
        from sources.proxmox import ProxmoxChecker
        from sources.truenas import TrueNASChecker
        from sources.opensuse import OpenSUSEChecker
        from sources.manjaro import ManjaroChecker
        from sources.endeavouros import EndeavourOSChecker
        from sources.mxlinux import MXLinuxChecker
        from sources.nixos import NixOSChecker
        from sources.freebsd import FreeBSDChecker
        from sources.tails import TailsChecker
        from sources.opnsense import OPNsenseChecker
        from sources.garuda import GarudaChecker
        from sources.popos import PopOSChecker
        from sources.zorin import ZorinChecker
        from sources.ubuntu_flavors import UbuntuFlavorsChecker
        from sources.kde_neon import KdeNeonChecker
        from sources.cachyos import CachyOSChecker
        from sources.deepin import DeepinChecker
        from sources.linux_lite import LinuxLiteChecker
        from sources.peppermint import PeppermintChecker
        from sources.lmde import LMDEChecker
        from sources.solus import SolusChecker
        from sources.antix import AntiXChecker
        from sources.sparkylinux import SparkyLinuxChecker
        from sources.q4os import Q4OSChecker
        from sources.mageia import MageiaChecker
        from sources.pclinuxos import PCLinuxOSChecker
        from sources.void_linux import VoidLinuxChecker
        from sources.slackware import SlackwareChecker
        from sources.gentoo import GentooChecker
        from sources.vanillaos import VanillaOSChecker
        from sources.parrot import ParrotChecker
        from sources.blackarch import BlackArchChecker
        from sources.qubes import QubesChecker
        from sources.alpine import AlpineChecker
        from sources.lakka import LakkaChecker
        from sources.openbsd import OpenBSDChecker
        from sources.netbsd import NetBSDChecker
        from sources.ghostbsd import GhostBSDChecker
        from sources.dragonflybsd import DragonFlyBSDChecker
        from sources.centos_stream import CentOSStreamChecker
        from sources.oracle_linux import OracleLinuxChecker
        from sources.pfsense import PfSenseChecker
        from sources.zentyal import ZentyalChecker
        from sources.univention import UniventionChecker
        from sources.systemrescue import SystemRescueChecker
        from sources.clonezilla import ClonezillaChecker
        from sources.gparted import GPartedChecker
        from sources.memtest86plus import Memtest86PlusChecker
        from sources.whonix import WhonixChecker
        from sources.hirens import HirensChecker
        from sources.elementary import ElementaryChecker

        _CHECKER_REGISTRY.update({
            "ubuntu":          UbuntuChecker,
            "debian":          DebianChecker,
            "fedora":          FedoraChecker,
            "linuxmint":       LinuxMintChecker,
            "arch":            ArchChecker,
            "kali":            KaliChecker,
            "rocky":           RockyChecker,
            "almalinux":       AlmaLinuxChecker,
            "windows":         WindowsChecker,
            "bazzite":         BazziteChecker,
            "nobara":          NobaraChecker,
            "chimeraos":       ChimeraOSChecker,
            "batocera":        BatoceraChecker,
            "proxmox":         ProxmoxChecker,
            "truenas":         TrueNASChecker,
            "opensuse":        OpenSUSEChecker,
            "manjaro":         ManjaroChecker,
            "endeavouros":     EndeavourOSChecker,
            "mxlinux":         MXLinuxChecker,
            "nixos":           NixOSChecker,
            "freebsd":         FreeBSDChecker,
            "tails":           TailsChecker,
            "opnsense":        OPNsenseChecker,
            "garuda":          GarudaChecker,
            "popos":           PopOSChecker,
            "zorin":           ZorinChecker,
            "ubuntu_flavors":  UbuntuFlavorsChecker,
            "kde_neon":        KdeNeonChecker,
            "cachyos":         CachyOSChecker,
            "deepin":          DeepinChecker,
            "linux_lite":      LinuxLiteChecker,
            "peppermint":      PeppermintChecker,
            "lmde":            LMDEChecker,
            "solus":           SolusChecker,
            "antix":           AntiXChecker,
            "sparkylinux":     SparkyLinuxChecker,
            "q4os":            Q4OSChecker,
            "mageia":          MageiaChecker,
            "pclinuxos":       PCLinuxOSChecker,
            "void_linux":      VoidLinuxChecker,
            "slackware":       SlackwareChecker,
            "gentoo":          GentooChecker,
            "vanillaos":       VanillaOSChecker,
            "parrot":          ParrotChecker,
            "blackarch":       BlackArchChecker,
            "qubes":           QubesChecker,
            "alpine":          AlpineChecker,
            "lakka":           LakkaChecker,
            "openbsd":         OpenBSDChecker,
            "netbsd":          NetBSDChecker,
            "ghostbsd":        GhostBSDChecker,
            "dragonflybsd":    DragonFlyBSDChecker,
            "centos_stream":   CentOSStreamChecker,
            "oracle_linux":    OracleLinuxChecker,
            "pfsense":         PfSenseChecker,
            "zentyal":         ZentyalChecker,
            "univention":      UniventionChecker,
            "systemrescue":    SystemRescueChecker,
            "clonezilla":      ClonezillaChecker,
            "gparted":         GPartedChecker,
            "memtest86plus":   Memtest86PlusChecker,
            "whonix":          WhonixChecker,
            "hirens":          HirensChecker,
            "elementary":      ElementaryChecker,
        })


def _check_one(iso: IsoEntry, distros_db: dict) -> CheckResult:
    _load_checkers()

    if iso.distro_id is None:
        return CheckResult(iso=iso, status=UpdateStatus.UNKNOWN)

    # Trouve la config de la distro dans la DB
    distro_cfg = next(
        (d for d in distros_db.get("distros", []) if d["id"] == iso.distro_id),
        None
    )
    if distro_cfg is None:
        return CheckResult(iso=iso, status=UpdateStatus.UNKNOWN)

    checker_id = distro_cfg.get("checker")
    variant = distro_cfg.get("checker_variant")

    checker_cls = _CHECKER_REGISTRY.get(checker_id)
    if checker_cls is None:
        return CheckResult(iso=iso, status=UpdateStatus.UNKNOWN)

    checker = checker_cls(variant=variant)

    # Distros sans API publique → vérification manuelle
    if checker_id in ("windows",):
        return CheckResult(iso=iso, status=UpdateStatus.MANUAL)

    try:
        latest = checker.get_latest_version()
    except Exception as e:
        return CheckResult(iso=iso, status=UpdateStatus.ERROR, error_msg=str(e))

    if latest is None:
        return CheckResult(iso=iso, status=UpdateStatus.ERROR, error_msg="Impossible de contacter la source")

    local_ver = iso.local_version
    if local_ver is None:
        local_ver = checker.parse_local_version(iso.filename)

    if local_ver is None:
        return CheckResult(iso=iso, status=UpdateStatus.UNKNOWN, latest_info=latest)

    try:
        outdated = checker.is_outdated(local_ver, latest.version)
    except Exception:
        outdated = local_ver != latest.version

    status = UpdateStatus.OUTDATED if outdated else UpdateStatus.UP_TO_DATE
    return CheckResult(iso=iso, status=status, latest_info=latest)


def check_all(
    iso_list: list[IsoEntry],
    distros_db: dict,
    on_result: Optional[Callable[[CheckResult], None]] = None,
    max_workers: int = 6,
) -> list[CheckResult]:
    """
    Vérifie toutes les ISO en parallèle.
    Appelle on_result(result) pour chaque résultat dès qu'il est disponible (thread-safe).
    """
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_check_one, iso, distros_db): iso
            for iso in iso_list
        }
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                iso = futures[future]
                result = CheckResult(iso=iso, status=UpdateStatus.ERROR, error_msg=str(e))
            results.append(result)
            if on_result:
                on_result(result)

    return results

🇬🇧 [English](CHANGELOG.md) · 🇫🇷 **Français**

# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [1.1.0] — 2026-08-22

### Ajouté
- **Support ARM64 en plus du x86_64** pour 13 distributions dont la source officielle publie un vrai ISO ARM64 générique, bootable via Ventoy (pas une image spécifique à une carte SBC) : Proxmox VE, AlmaLinux, CentOS Stream 9/10, Rocky Linux, Debian, FreeBSD, Gentoo, openSUSE Tumbleweed, Kali Linux, Oracle Linux, Alpine Linux, Void Linux (glibc+musl), Ubuntu Server. Le x86_64 reste la cible prioritaire par défaut partout ; chaque build ARM64 apparaît comme une entrée distincte clairement étiquetée « (ARM64) », jamais mélangée avec son équivalent x86_64. 123 variantes enregistrées, contre 108 auparavant.

### Corrigé
- **Void Linux (glibc)** : le motif de nom de fichier ne correspondait plus aux vrais fichiers téléchargés par le vérificateur lui-même (suffixe `-base`/`-xfce`/etc. manquant) — la détection de version locale était silencieusement cassée.
- **CentOS Stream 9/10** : le motif x86_64 était assez large pour aussi correspondre à un fichier aarch64 présent sur la même clé USB, ce qui allait à l'encontre du but recherché (différencier les deux architectures).

## [1.0.1] — 2026-08-22

### Corrigé
- **Proxmox VE** : le répertoire officiel liste désormais un ISO arm64 (`proxmox-ve_9.2-1-arm64.iso`) à côté du build amd64 classique. L'expression régulière ne l'évitait que par accident (pas d'ancrage explicite sur l'architecture) — durcie pour rejeter explicitement tout fichier contenant `arm`.
- Correction associée : déduplication des résultats — la page source répète chaque nom de fichier plusieurs fois (lien, taille, date), ce qui produisait auparavant 5 à 10 entrées en double par version dans le navigateur de versions.

### Interne
- Tous les commentaires de code, docstrings et messages de log de diagnostic traduits en anglais (auparavant en français en premier). Aucun effet sur l'interface ou le comportement de l'application — le switch français/anglais visible par l'utilisateur n'est pas concerné.

[1.1.0]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.0...v1.0.1

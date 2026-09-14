🇬🇧 [English](CHANGELOG.md) · 🇫🇷 **Français**

# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.
Format basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [1.1.2] — 2026-09-14

### Ajouté
- **Bouton « Copier » sur le journal d'installation de Ventoy** : la sortie de `Ventoy2Disk.sh` (ou l'erreur qui l'a interrompu) peut désormais être copiée dans le presse-papiers directement depuis l'assistant « Créer une clé Ventoy », au lieu de devoir sélectionner le texte à la main.

### Changé
- **Les fenêtres de confirmation/erreur/info correspondent désormais au thème sombre de l'appli** : chacune d'entre elles (~25 endroits dans le code) passait par `tkinter.messagebox`, qui s'affiche toujours avec le rendu natif de Tk (fond clair, boutons natifs) — jurant avec le reste de l'interface. Remplacées par une boîte de dialogue personnalisée basée sur `CTkToplevel` (`gui/dialogs.py`), stylée comme le reste de l'appli, avec une icône colorée selon la gravité (info/avertissement/erreur/question) et un accent rouge sur les confirmations destructrices (suppression d'un fichier, effacement d'une clé USB).

### Corrigé
- **La fenêtre « Créer une clé Ventoy » était coupée en bas, cachant le bouton Installer** : la boîte de dialogue avait une taille fixe et non redimensionnable de `620x520`. Son contenu réel nécessite déjà environ 644px à l'échelle d'affichage normale (1x), et chaque widget grandit encore davantage avec une mise à l'échelle/DPI plus élevée — un cas fréquent sur les bureaux Linux — si bien que les boutons Installer/Fermer en bas pouvaient se retrouver entièrement hors fenêtre, sans aucun moyen de redimensionner pour les atteindre. Corrigé en dimensionnant la fenêtre d'après sa hauteur réellement nécessaire au démarrage et en la rendant redimensionnable : elle s'ouvre désormais toujours assez haute pour montrer tous les boutons, et peut être redimensionnée davantage si besoin.
- **Le téléchargement de Ventoy était oublié à chaque réouverture de l'assistant « Créer une clé Ventoy »** : le téléchargement allait dans un dossier temporaire jetable (`tempfile.mkdtemp()`) que seule l'instance de boîte de dialogue en cours connaissait. Fermer l'assistant puis le rouvrir (ou même simplement laisser le système nettoyer `/tmp`) faisait à nouveau afficher « Ventoy non trouvé localement », forçant un nouveau téléchargement complet — et comme rien ne re-sélectionnait ensuite automatiquement la clé USB, on pouvait avoir l'impression que le téléchargement « ne faisait rien », alors qu'il s'était simplement répété. Corrigé en téléchargeant dans un cache persistant (`~/.local/share/ventoyisoupdater/ventoy/`), consulté à la fois par l'étape de téléchargement et par la vérification « déjà installé ? » : une copie déjà téléchargée est désormais retrouvée immédiatement et le bouton Installer est prêt tout de suite. L'archive devenue inutile est aussi supprimée juste après l'extraction plutôt que d'être laissée sur le disque à chaque téléchargement.
- **L'installation de Ventoy ne faisait silencieusement rien sur Linux** : `Ventoy2Disk.sh` demande toujours une confirmation « Continue? (y/n) » sur son entrée standard avant d'effacer le disque (deux fois, pour une installation simple), et n'a aucune option pour la sauter. L'appli l'exécutait sans jamais répondre à cette question : selon la façon dont l'entrée standard était héritée, soit ça restait bloqué jusqu'au timeout de 2 minutes, soit ça recevait immédiatement un EOF, interprété comme un « non », et le script se terminait avec le code 0 — que l'appli rapportait alors comme une installation **réussie**, alors que le disque n'avait jamais été touché. Corrigé en fournissant automatiquement la confirmation (le même avertissement est déjà affiché à l'utilisateur au préalable, dans la boîte de dialogue de confirmation de l'appli), et le délai a été porté à 180 s.
- **L'installation de Ventoy échouait systématiquement sur Linux** : le code recherchait le script d'installation sous le nom `ventoy2disk.sh`, alors que l'archive officielle Ventoy pour Linux le fournit sous le nom `Ventoy2Disk.sh` (casse mixte). Sur tout système de fichiers sensible à la casse (ext4, btrfs, xfs — donc pratiquement toutes les distributions Linux, Fedora compris), la recherche ne trouvait jamais de correspondance : `find_ventoy_in_dir`/`find_ventoy_binary` ne renvoyaient jamais rien, et l'appli affichait « Ventoy2Disk.sh introuvable » même juste après avoir téléchargé et extrait une copie toute fraîche. Corrigé en recherchant le vrai nom de fichier (les deux casses sont désormais acceptées, au cas où un paquet tiers utiliserait la forme en minuscules).

## [1.1.1] — 2026-08-23

### Corrigé
- **Échec du téléchargement du logo pour 4 distros** (Kali, AlmaLinux, Manjaro, Nobara) : `logo_url` pointait vers un fichier `.svg`, un format que PIL ne sait pas du tout décoder — chaque tentative de synchronisation de logo échouait avec une erreur brute `cannot identify image file`, pour tous les utilisateurs, à chaque fois. Corrigé en embarquant un vrai PNG pour chacune dans `assets/logos/` (même mécanisme déjà utilisé pour Proxmox/Pop!_OS) plutôt que de dépendre d'une URL vectorielle.

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

[1.1.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/celmax85/VentoyIsoUpdater/compare/v1.0.0...v1.0.1

🇬🇧 [English](SECURITY.md) · 🇫🇷 **Français**

# Politique de sécurité

VentoyIsoUpdater télécharge des fichiers exécutables (l'installeur Ventoy) et
peut demander une élévation de privilèges (`pkexec`/`sudo` sur Linux, droits
administrateur sur Windows) pour installer Ventoy sur une clé USB. Toute
faille touchant ce chemin — téléchargement, vérification d'intégrité,
extraction d'archive, exécution — est traitée en priorité.

## Signaler une vulnérabilité

Merci de **ne pas** ouvrir d'issue publique pour un problème de sécurité.
Contactez à la place : **maxencebaffet@pratimedia.com**

Merci d'inclure si possible :
- une description du problème et de son impact ;
- les étapes pour le reproduire ;
- la version de VentoyIsoUpdater et l'OS concernés.

## Délai de réponse

Accusé de réception sous 7 jours. Un correctif ou un plan de correction sera
communiqué avant toute divulgation publique.

## Périmètre

Sont notamment dans le périmètre :
- `core/ventoy_installer.py` (téléchargement, vérification d'intégrité et
  exécution privilégiée de l'installeur Ventoy) ;
- `core/downloader.py` (téléchargement et vérification des ISO/logos) ;
- les vérificateurs de `sources/` (requêtes réseau vers des sources tierces).

Les failles des sites tiers interrogés par `sources/` (Ubuntu, Debian, etc.)
ne relèvent pas de ce dépôt — merci de les signaler directement au projet
concerné.

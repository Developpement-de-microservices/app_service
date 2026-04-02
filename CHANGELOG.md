# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [2.0] - 02/04/2026
### Added
- Implémentation de MongoDB

### Changed
- Suppression du fonctionnement de DB en JSON au profit de MongoDB
- Image allégée à l'aide d'une version basée sur alpine

### Fixed
- N/A

## [1.0] - 31/03/2026
### Added
- L'ensemble des fichiers source du microservice se trouve dans le dossier app
- Ce dossier contient le Dockerfile qui permet de construire le microservice
- Le code source du service se trouve dans app.py
- Les dépendances se trouvent dans requirements.txt, et sont automatiquement installées lors du build de l'image
- Création du service **Apps** en Flask.
- Gestion des applications :
  - Liste de toutes les applications (`/apps` - GET)
  - Création d’une application (`/apps` - POST)
  - - Affichage des détails d'une application (`/apps/<app_id>` - GET)
  - Modification d'une application (`/apps/<app_id>` - PATCH)
  - Suppression d'une application (`/apps/<app_id>` - DELETE)
  - Récupération des versions d'une application par son ID (`/apps/<app_id>/versions` - GET)
  - Création d'une version pour une application donnée (`/apps/<app_id>/versions` - POST)
  - Récupération du détail d'une version par son ID (`/apps/<app_id>/versions/<version_id>` - GET)
  - Modification d'une version par son ID (`/apps/<app_id>/versions/<version_id>` - PATCH)
  - Suppression d'une version par son ID (`/apps/<app_id>/versions/<version_id>` - DELETE)
- Stockage persistant des applications dans `data/apps.json` et des versions dans `data/versions.json`.
- Authentification et vérification des tokens via le service `/auth/verify`.
- Endpoint **health** pour le service Apps (`/apps/health`).


### Changed
- N/A (première version)

### Fixed
- N/A (première version)

# 🚀 Service de Gestion d'Applications (App Management API)

Microservice **Python 3.11** haute performance dédié à la centralisation des catalogues d'applications et au suivi de leur cycle de vie (versioning). Conçu pour une intégration native en environnement conteneurisé.

---

## ✨ Fonctionnalités Clés
* **Gestion granulaire (CRUD)** : Contrôle total sur les entités "Applications" et "Versions".
* **Persistance Fluide** : Stockage asynchrone dans des fichiers JSON localisés dans `/app/data`.
* **Identifiants Robustes** : Utilisation de UUID pour garantir l'unicité globale des ressources.
* **Empreinte Optimisée** : Image basée sur `python:3.11-slim` pour minimiser la surface d'attaque et le temps de déploiement.

---

## 🔐 Sécurité & Flux d'Authentification
Le service implémente une couche de sécurité stricte via le décorateur `@require_auth`.

* **Mécanisme** : Authentification par jeton (Bearer Token).
* **Validation Déléguée** : Chaque requête est validée en amont par un service de proxy (`http://proxy/auth/verify`).
* **Résilience** : Gestion native des indisponibilités du service d'authentification (Erreur 503) et des accès non autorisés (Erreur 401).

---

## 📖 Spécifications de l'API

### 📱 Ressources : Applications
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/apps` | Récupère la liste exhaustive des applications. |
| **POST** | `/apps` | Enregistre une nouvelle application (**Nom requis**). |
| **GET** | `/apps/<id>` | Détails techniques d'une application spécifique. |
| **PATCH** | `/apps/<id>` | Mise à jour partielle des métadonnées. |
| **DELETE** | `/apps/<id>` | Suppression de l'application et de ses versions liées. |

### 📦 Ressources : Versions
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/apps/<id>/versions` | Liste l'historique complet des versions d'une app. |
| **POST** | `/apps/<id>/versions` | Publie une nouvelle version (**Version requise**). |
| **GET** | `/apps/<id>/v_id` | Détails d'une version spécifique. |
| **PATCH** | `/apps/<id>/v_id` | Modification (status, changelog, etc.). |
| **DELETE** | `/apps/<id>/v_id` | Retrait d'une version spécifique du catalogue. |

---

## 🏥 Surveillance & Docker Healthcheck
Le service expose un point de terminaison de santé conforme aux exigences de [Flask](https://flask.palletsprojects.com/) et de l'orchestration Docker.

* **Endpoint** : `/apps/health` (Exclu du middleware d'authentification).
* **Configuration Docker** :
    * **Intervalle** : 30 secondes.
    * **Timeout** : 5 secondes.
    * **Seuil d'échec** : 3 tentatives.
* **Action** : Un `curl` interne vérifie la disponibilité du port `5001`.

---

## 🛠 Détails Techniques & Maintenance
* **Image de base** : `python:3.11-slim`
* **Maintainer** : Florent L. (`flo-lec`)
* **Service Label** : `app_service`
* **Port d'exposition** : `5001`
* **Librairies majeures** : Flask-CORS, `requests`, `uuid`.

### Schéma de données (Exemple)
```json
{
    "id": "e4e9f738-9b4a-4a2e-8c3d-1a2b3c4d5e6f",
    "applicationId": "app-uuid-123",
    "status": "PUBLISHED",
    "version": "2.1.0-stable",
    "changelog": "Correction des bugs mineurs et optimisation SQL.",
    "createdAt": "2026-03-31T15:00:00Z"
}

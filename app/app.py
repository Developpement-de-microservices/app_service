from datetime import datetime, timezone
from functools import wraps
from flask_cors import CORS
import requests
import uuid
from flask import Flask, request, jsonify
import os
import json

server = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
APPS_DB_FILE = os.path.join(DATA_DIR, 'apps.json')
VERSIONS_DB_FILE = os.path.join(DATA_DIR, 'versions.json')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CORS(server)



def open_apps_db():
    try:
        if not os.path.exists(APPS_DB_FILE): return {}
        with open(APPS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_apps_db(app_dict):
    try:
        with open(APPS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_dict, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


def open_versions_db():
    try:
        if not os.path.exists(VERSIONS_DB_FILE): return {}
        with open(VERSIONS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_versions_db(app_dict):
    try:
        with open(VERSIONS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(app_dict, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_unique_uuid():
    apps = open_apps_db()
    versions = open_versions_db()
    while True:
        new_id = str(uuid.uuid4())
        if new_id not in apps.keys() and all(new_id not in app_versions for app_versions in versions.values()):
            return new_id

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token manquant ou format invalide"}), 401

        token = auth_header.replace("Bearer ", "")
        try:
            response = requests.post("http://proxy/auth/verify",
                                     headers={"Authorization": f"Bearer {token}"},
                                     timeout=5)
            if response.status_code != 200:
                return jsonify({"error": "Non autorisé"}), 401
        except requests.RequestException:
            return jsonify({"error": "Service d'authentification indisponible"}), 503
        return f(*args, **kwargs)

    return decorated

@server.route('/apps', methods=['GET'])
@require_auth
def get_apps():
    return jsonify(open_apps_db()), 200


@server.route('/apps', methods=['POST'])
@require_auth
def post_apps():
    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    if not data.get('name'):
        return jsonify({"message": "Le champ 'name' est obligatoire"}), 400

    apps = open_apps_db()
    gen_id = get_unique_uuid()

    new_app = {
        "id": gen_id,
        "name": data.get('name'),
        "description": data.get('description', 'N/A'),
        "repositoryUrl": data.get('repositoryUrl', 'N/A'),
        "ownerId": data.get('ownerId', 'N/A'),
        "latestVersion": data.get('latestVersion', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    apps[gen_id] = new_app
    if not save_apps_db(apps):
        return jsonify({"message": "Erreur lors de la sauvegarde"}), 500

    return jsonify({"id": gen_id, "message": "Application ajoutée avec succès", "app": new_app}), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
@require_auth
def get_app(app_id):
    apps = open_apps_db()
    app = apps.get(app_id)
    if not app:
        return jsonify({"message": "Pas d'application avec cet ID"}), 404
    return jsonify(app), 200


@server.route('/apps/<string:app_id>', methods=['PATCH'])
@require_auth
def patch_app(app_id):
    apps = open_apps_db()
    if app_id not in apps:
        return jsonify({"message": "Non trouvé"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    app = apps[app_id]
    fields = ['name', 'description', 'repositoryUrl', 'ownerId', 'latestVersion']
    for field in fields:
        if field in data:
            app[field] = data[field]

    app["updatedAt"] = datetime.now(timezone.utc).isoformat()

    save_apps_db(apps)
    return jsonify({"id": app_id, "message": "Application modifiée", "app": app}), 200


@server.route('/apps/<string:app_id>', methods=['DELETE'])
@require_auth
def delete_app(app_id):
    apps = open_apps_db()
    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    apps.pop(app_id)
    versions = open_versions_db()
    if app_id in versions:
        versions.pop(app_id)
        save_versions_db(versions)

    save_apps_db(apps)
    return jsonify({"id": app_id, "message": "Application supprimée avec succès"}), 200

@server.route('/apps/<string:app_id>/versions', methods=['GET'])
@require_auth
def get_versions(app_id):
    if app_id not in open_apps_db():
        return jsonify({"message": "Application non trouvée"}), 404

    versions = open_versions_db()
    return jsonify(versions.get(app_id, {})), 200


@server.route('/apps/<string:app_id>/versions', methods=['POST'])
@require_auth
def post_versions(app_id):
    if app_id not in open_apps_db():
        return jsonify({"message": "Application non trouvée"}), 404

    data = request.json
    if not data or not data.get('version'):
        return jsonify({"message": "Le champ 'version' est obligatoire"}), 400

    versions = open_versions_db()
    gen_id = get_unique_uuid()

    if app_id not in versions:
        versions[app_id] = {}

    new_version = {
        "id": gen_id,
        "applicationId": app_id,
        "status": data.get('status', 'DRAFT'),
        "version": data.get('version'),
        "changelog": data.get('changelog', 'N/A'),
        "versionUrl": data.get('versionUrl', 'N/A'),
        "ownerId": data.get('ownerId', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    versions[app_id][gen_id] = new_version
    save_versions_db(versions)

    return jsonify({
        "id": gen_id,
        "applicationId": app_id,
        "message": "Version ajoutée avec succès",
        "version": new_version
    }), 201


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['GET'])
@require_auth
def get_version(app_id, version_id):
    if app_id not in open_apps_db():
        return jsonify({"message": "Application non trouvée"}), 404

    app_versions = open_versions_db().get(app_id, {})
    version = app_versions.get(version_id)

    if not version:
        return jsonify({"message": "Version non trouvée"}), 404

    return jsonify(version), 200


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['PATCH'])
@require_auth
def patch_version(app_id, version_id):
    if app_id not in open_apps_db():
        return jsonify({"message": "Application non trouvée"}), 404

    versions = open_versions_db()
    app_versions = versions.get(app_id, {})
    if version_id not in app_versions:
        return jsonify({"message": "Version non trouvée"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    version = app_versions[version_id]
    fields = ['status', 'version', 'changelog', 'versionUrl', 'ownerId']
    for field in fields:
        if field in data:
            version[field] = data[field]

    version["updatedAt"] = datetime.now(timezone.utc).isoformat()
    save_versions_db(versions)

    return jsonify({
        "id": version_id,
        "applicationId": app_id,
        "message": "Version modifiée",
        "version": version
    }), 200


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['DELETE'])
@require_auth
def delete_version(app_id, version_id):
    versions = open_versions_db()
    app_versions = versions.get(app_id, {})

    if version_id not in app_versions:
        return jsonify({"message": "Version non trouvée"}), 404

    app_versions.pop(version_id)
    if not app_versions:
        versions.pop(app_id)

    save_versions_db(versions)
    return jsonify({"id": version_id, "message": "Version supprimée avec succès"}), 200


@server.route("/apps/health", methods=["GET"])
def get_health_apps():
    return jsonify({
        "status": "ok",
        "service": "Apps",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5001, debug=True)
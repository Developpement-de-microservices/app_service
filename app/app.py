from datetime import datetime, timezone

import uuid
from flask import Flask, request, jsonify
import os
import json

server = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DB_FILE = os.path.join(BASE_DIR, 'apps.json')
VERSIONS_DB_FILE = os.path.join(BASE_DIR, 'versions.json')

def open_apps_db():
    try:
        with open(APPS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_apps_db(app_dict):
    with open(APPS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(app_dict, f, indent=4, ensure_ascii=False)

def open_versions_db():
    try:
        with open(VERSIONS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_versions_db(app_dict):
    with open(VERSIONS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(app_dict, f, indent=4, ensure_ascii=False)

def get_unique_uuid():
    apps = open_apps_db()
    versions = open_versions_db()
    while True:
        new_id = str(uuid.uuid4())
        if new_id not in apps.keys() and all(new_id not in app_versions for app_versions in versions.values()):
            return new_id


@server.route('/apps', methods=['GET'])
def get_apps():
    return jsonify(open_apps_db()), 200


@server.route('/apps', methods=['POST'])
def post_apps():
    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    apps = open_apps_db()

    gen_id = get_unique_uuid()

    apps[gen_id] = {
        "id": gen_id,
        "name": data.get('name', 'N/A'),
        "description": data.get('description', 'N/A'),
        "repositoryUrl": data.get('repositoryUrl', 'N/A'),
        "ownerId": data.get('ownerId', 'N/A'),
        "latestVersion": data.get('latestVersion', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    save_apps_db(apps)

    return jsonify({
        "id": gen_id,
        "message": "Application ajoutée avec succès"
    }), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
def get_app(app_id):
    apps = open_apps_db()
    app = apps.get(app_id)
    if app:
        return jsonify(app), 200

    return jsonify({
        "message": "Pas d'application avec cet ID"
    }), 404


@server.route('/apps/<string:app_id>', methods=['DELETE'])
def delete_app(app_id):
    apps = open_apps_db()
    versions = open_versions_db()

    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    apps.pop(app_id)
    if app_id in versions:
        versions.pop(app_id)

    save_apps_db(apps)
    save_versions_db(versions)

    return jsonify({
        "id": app_id,
        "message": "Application supprimée avec succès"
    }), 200


@server.route('/apps/<string:app_id>', methods=['PATCH'])
def patch_app(app_id):
    apps = open_apps_db()
    if app_id not in apps:
        return jsonify({"message": "Non trouvé"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    apps[app_id].update({
        "name": data.get('name', apps[app_id]['name']),
        "description": data.get('description', apps[app_id]['description']),
        "repositoryUrl": data.get('repositoryUrl', apps[app_id]['repositoryUrl']),
        "ownerId": data.get('ownerId', apps[app_id]['ownerId']),
        "latestVersion": data.get('latestVersion', apps[app_id]['latestVersion']),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    })

    save_apps_db(apps)
    return jsonify({
        "id": app_id,
        "message": "Application modifiée",
        "app": apps[app_id]
    }), 200

@server.route('/apps/<string:app_id>/versions', methods=['GET'])
def get_versions(app_id):
    apps = open_apps_db()
    versions = open_versions_db()

    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    app_versions = versions.get(app_id)
    if not app_versions:
        return jsonify({}), 200

    return jsonify(app_versions), 200


@server.route('/apps/<string:app_id>/versions', methods=['POST'])
def post_versions(app_id):
    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    apps = open_apps_db()
    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    versions = open_versions_db()
    gen_id = get_unique_uuid()

    if app_id not in versions:
        versions[app_id] = {}

    versions[app_id][gen_id] = {
        "id": gen_id,
        "applicationId": app_id,
        "status": data.get('status', 'N/A'),
        "version": data.get('version', 'N/A'),
        "changelog": data.get('changelog', 'N/A'),
        "versionUrl": data.get('versionUrl', 'N/A'),
        "ownerId": data.get('ownerId', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    save_versions_db(versions)

    return jsonify({
        "id": gen_id,
        "applicationId": app_id,
        "message": "Version ajoutée avec succès"
    }), 201

@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['GET'])
def get_version(app_id, version_id):
    apps = open_apps_db()
    versions = open_versions_db()

    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    app_versions = versions.get(app_id)
    if not app_versions:
        return jsonify({"message": "Aucune version trouvée pour cette application"}), 404

    version = app_versions.get(version_id)
    if not version:
        return jsonify({"message": "Version non trouvée"}), 404

    return jsonify(version), 200


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['PATCH'])
def patch_version(app_id, version_id):
    apps = open_apps_db()
    versions = open_versions_db()

    if app_id not in apps:
        return jsonify({"message": "Application non trouvée"}), 404

    app_versions = versions.get(app_id)
    if not app_versions:
        return jsonify({"message": "Aucune version trouvée pour cette application"}), 404

    version = app_versions.get(version_id)
    if not version:
        return jsonify({"message": "Version non trouvée"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    version.update({
        "status": data.get("status", version["status"]),
        "version": data.get("version", version["version"]),
        "changelog": data.get("changelog", version["changelog"]),
        "versionUrl": data.get("versionUrl", version["versionUrl"]),
        "ownerId": data.get("ownerId", version["ownerId"]),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    })

    save_versions_db(versions)

    return jsonify({
        "id": version_id,
        "applicationId": app_id,
        "message": "Version modifiée",
        "version": version
    }), 200

@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['DELETE'])
def delete_version(app_id, version_id):
    versions = open_versions_db()

    app_versions = versions.get(app_id)
    if not app_versions:
        return jsonify({"message": "Aucune version trouvée pour cette application"}), 404

    if version_id not in app_versions:
        return jsonify({"message": "Version non trouvée"}), 404

    app_versions.pop(version_id)
    if not app_versions:
        versions.pop(app_id)

    save_versions_db(versions)

    return jsonify({
        "id": version_id,
        "message": "Version supprimée avec succès"
    }), 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5001, debug=True)
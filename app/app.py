from datetime import datetime, timezone
from functools import wraps
from flask_cors import CORS
import requests
import uuid
from flask import Flask, request, jsonify, g
import os
from pymongo import MongoClient

server = Flask(__name__)

client_db = MongoClient(os.getenv("MONGO_URI", "mongodb://db_app_service:27017/"))
db = client_db['app_db']
apps_col = db['apps']
versions_col = db['versions']

CORS(server)



def get_unique_uuid():
    while True:
        new_id = str(uuid.uuid4())
        if not apps_col.find_one({"_id": new_id}) and not versions_col.find_one({"_id": new_id}):
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
            if response.status_code == 200:
                data = response.json()
                g.user_id = data.get("user_id")
        except requests.RequestException:
            return jsonify({"error": "Service d'authentification indisponible"}), 503
        return f(*args, **kwargs)

    return decorated

@server.route('/apps', methods=['GET'])
@require_auth
def get_apps():
    apps = list(apps_col.find())
    return jsonify(apps), 200


@server.route('/apps', methods=['POST'])
@require_auth
def post_apps():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"message": "Le champ 'name' est obligatoire"}), 400

    gen_id = get_unique_uuid()
    new_app = {
        "_id": gen_id,
        "name": data.get('name'),
        "description": data.get('description', 'N/A'),
        "repositoryUrl": data.get('repositoryUrl', 'N/A'),
        "ownerId": g.user_id,
        "latestVersion": data.get('latestVersion', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    apps_col.insert_one(new_app)
    return jsonify({"id": gen_id, "message": "Application ajoutée", "app": new_app}), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
@require_auth
def get_app(app_id):
    app = apps_col.find_one({"_id": app_id})
    if not app:
        return jsonify({"message": "Pas d'application avec cet ID"}), 404
    return jsonify(app), 200


@server.route('/apps/<string:app_id>', methods=['PATCH'])
@require_auth
def patch_app(app_id):
    data = request.json
    if not data:
        return jsonify({"message": "Corps de requête JSON manquant"}), 400

    fields = ['name', 'description', 'repositoryUrl', 'latestVersion']
    updates = {k: v for k, v in data.items() if k in fields}

    if not updates:
        return jsonify({"message": "Aucune donnée valide à modifier"}), 400

    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = apps_col.update_one({"_id": app_id}, {"$set": updates})

    if result.matched_count == 0:
        return jsonify({"message": "Non trouvé"}), 404

    updated_app = apps_col.find_one({"_id": app_id})
    return jsonify({"id": app_id, "message": "Application modifiée", "app": updated_app}), 200


@server.route('/apps/<string:app_id>', methods=['DELETE'])
@require_auth
def delete_app(app_id):
    result = apps_col.delete_one({"_id": app_id})
    if result.deleted_count == 0:
        return jsonify({"message": "Application non trouvée"}), 404

    versions_col.delete_many({"applicationId": app_id})

    return jsonify({"id": app_id, "message": "Application et ses versions supprimées"}), 200

@server.route('/apps/<string:app_id>/versions', methods=['GET'])
@require_auth
def get_versions(app_id):
    if not apps_col.find_one({"_id": app_id}):
        return jsonify({"message": "Application non trouvée"}), 404

    versions = list(versions_col.find({"applicationId": app_id}))
    return jsonify(versions), 200


@server.route('/apps/<string:app_id>/versions', methods=['POST'])
@require_auth
def post_versions(app_id):
    if not apps_col.find_one({"_id": app_id}):
        return jsonify({"message": "Application non trouvée"}), 404

    data = request.json
    if not data or not data.get('version'):
        return jsonify({"message": "Le champ 'version' est obligatoire"}), 400

    gen_id = get_unique_uuid()
    new_version = {
        "_id": gen_id,
        "applicationId": app_id,
        "status": data.get('status', 'DRAFT'),
        "version": data.get('version'),
        "changelog": data.get('changelog', 'N/A'),
        "versionUrl": data.get('versionUrl', 'N/A'),
        "ownerId": g.user_id,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    versions_col.insert_one(new_version)
    return jsonify({"id": gen_id, "applicationId": app_id, "version": new_version}), 201


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['GET'])
@require_auth
def get_version(app_id, version_id):
    version = versions_col.find_one({"_id": version_id, "applicationId": app_id})
    if not version:
        return jsonify({"message": "Version non trouvée"}), 404
    return jsonify(version), 200


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['PATCH'])
@require_auth
def patch_version(app_id, version_id):
    data = request.json
    fields = ['status', 'version', 'changelog', 'versionUrl']
    updates = {k: v for k, v in data.items() if k in fields}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    result = versions_col.update_one(
        {"_id": version_id, "applicationId": app_id},
        {"$set": updates}
    )

    if result.matched_count == 0:
        return jsonify({"message": "Version non trouvée"}), 404

    updated_version = versions_col.find_one({"_id": version_id})
    return jsonify({"id": version_id, "version": updated_version}), 200


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['DELETE'])
@require_auth
def delete_version(app_id, version_id):
    result = versions_col.delete_one({"_id": version_id, "applicationId": app_id})
    if result.deleted_count == 0:
        return jsonify({"message": "Version non trouvée"}), 404

    return jsonify({"id": version_id, "message": "Version supprimée"}), 200


# --- HEALTH ---

@server.route("/apps/health", methods=["GET"])
def get_health_apps():
    return jsonify({
        "status": "ok",
        "service": "Apps-MongoDB",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5001, debug=True)
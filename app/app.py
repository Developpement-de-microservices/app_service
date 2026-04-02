from datetime import datetime, timezone
from functools import wraps
from flask_cors import CORS
import requests
import os
from flask import Flask, request, jsonify, g
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId

server = Flask(__name__)
client_db = MongoClient(os.getenv("MONGO_URI", "mongodb://db_app_service:27017/"))
db = client_db['app_db']
apps_col = db['apps']
versions_col = db['versions']

CORS(server)

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
    for app in apps:
        app["_id"] = str(app["_id"])
    return jsonify(apps), 200


@server.route('/apps', methods=['POST'])
@require_auth
def post_apps():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({"message": "Le champ 'name' est obligatoire"}), 400

    new_app = {
        "name": data.get('name'),
        "description": data.get('description', 'N/A'),
        "repositoryUrl": data.get('repositoryUrl', 'N/A'),
        "ownerId": g.user_id,
        "latestVersion": data.get('latestVersion', 'N/A'),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    result = apps_col.insert_one(new_app)
    inserted_id = str(result.inserted_id)
    new_app["_id"] = inserted_id
    return jsonify({"id": inserted_id, "message": "Application ajoutée", "app": new_app}), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
@require_auth
def get_app(app_id):
    try:
        app = apps_col.find_one({"_id": ObjectId(app_id)})
        if not app:
            return jsonify({"message": "Pas d'application avec cet ID"}), 404
        app["_id"] = str(app["_id"])
        return jsonify(app), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>', methods=['PATCH'])
@require_auth
def patch_app(app_id):
    try:
        data = request.json
        if not data:
            return jsonify({"message": "Corps de requête JSON manquant"}), 400

        fields = ['name', 'description', 'repositoryUrl', 'latestVersion']
        updates = {k: v for k, v in data.items() if k in fields}

        if not updates:
            return jsonify({"message": "Aucune donnée valide à modifier"}), 400

        updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

        result = apps_col.update_one({"_id": ObjectId(app_id)}, {"$set": updates})

        if result.matched_count == 0:
            return jsonify({"message": "Non trouvé"}), 404

        updated_app = apps_col.find_one({"_id": ObjectId(app_id)})
        updated_app["_id"] = str(updated_app["_id"])
        return jsonify({"id": app_id, "message": "Application modifiée", "app": updated_app}), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>', methods=['DELETE'])
@require_auth
def delete_app(app_id):
    try:
        oid = ObjectId(app_id)
        result = apps_col.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return jsonify({"message": "Application non trouvée"}), 404

        versions_col.delete_many({"applicationId": oid})

        return jsonify({"id": app_id, "message": "Application et ses versions supprimées"}), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400

@server.route('/apps/<string:app_id>/versions', methods=['GET'])
@require_auth
def get_versions(app_id):
    try:
        oid = ObjectId(app_id)
        if not apps_col.find_one({"_id": oid}):
            return jsonify({"message": "Application non trouvée"}), 404

        versions = list(versions_col.find({"applicationId": oid}))
        for v in versions:
            v["_id"] = str(v["_id"])
            v["applicationId"] = str(v["applicationId"])
        return jsonify(versions), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>/versions', methods=['POST'])
@require_auth
def post_versions(app_id):
    try:
        oid = ObjectId(app_id)
        if not apps_col.find_one({"_id": oid}):
            return jsonify({"message": "Application non trouvée"}), 404

        data = request.json
        if not data or not data.get('version'):
            return jsonify({"message": "Le champ 'version' est obligatoire"}), 400

        new_version = {
            "applicationId": oid,
            "status": data.get('status', 'DRAFT'),
            "version": data.get('version'),
            "changelog": data.get('changelog', 'N/A'),
            "versionUrl": data.get('versionUrl', 'N/A'),
            "ownerId": g.user_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }

        result = versions_col.insert_one(new_version)
        v_id = str(result.inserted_id)
        new_version["_id"] = v_id
        new_version["applicationId"] = str(new_version["applicationId"])

        return jsonify({"id": v_id, "applicationId": app_id, "message": "Version ajoutée", "version": new_version}), 201
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['GET'])
@require_auth
def get_version(app_id, version_id):
    try:
        version = versions_col.find_one({
            "_id": ObjectId(version_id), 
            "applicationId": ObjectId(app_id)
        })
        if not version:
            return jsonify({"message": "Version non trouvée"}), 404
        
        version["_id"] = str(version["_id"])
        version["applicationId"] = str(version["applicationId"])
        return jsonify(version), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['PATCH'])
@require_auth
def patch_version(app_id, version_id):
    try:
        data = request.json
        fields = ['status', 'version', 'changelog', 'versionUrl']
        updates = {k: v for k, v in data.items() if k in fields}
        updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

        result = versions_col.update_one(
            {"_id": ObjectId(version_id), "applicationId": ObjectId(app_id)},
            {"$set": updates}
        )

        if result.matched_count == 0:
            return jsonify({"message": "Version non trouvée"}), 404

        updated_version = versions_col.find_one({"_id": ObjectId(version_id)})
        updated_version["_id"] = str(updated_version["_id"])
        updated_version["applicationId"] = str(updated_version["applicationId"])
        
        return jsonify({
            "id": version_id, 
            "applicationId": app_id, 
            "message": "Version modifiée", 
            "version": updated_version
        }), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400


@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['DELETE'])
@require_auth
def delete_version(app_id, version_id):
    try:
        result = versions_col.delete_one({
            "_id": ObjectId(version_id), 
            "applicationId": ObjectId(app_id)
        })
        if result.deleted_count == 0:
            return jsonify({"message": "Version non trouvée"}), 404

        return jsonify({"id": version_id, "message": "Version supprimée"}), 200
    except InvalidId:
        return jsonify({"message": "Format d'ID invalide"}), 400

# --- HEALTH ---

@server.route("/apps/health", methods=["GET"])
def get_health_apps():
    return jsonify({
        "status": "ok",
        "service": "Apps",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5001, debug=True)
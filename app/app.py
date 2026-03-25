from datetime import datetime, timezone

import uuid
from flask import Flask, request, jsonify
import os
import json

server = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'data.json')


def open_apps_data():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_apps(app_dict):
    with open(DB_FILE, 'w') as f:
        json.dump(app_dict, f, indent=4)

def get_unique_uuid():
    apps = open_apps_data()
    while True:
        new_id = str(uuid.uuid4())
        if new_id not in apps.keys():
            return new_id


@server.route('/apps', methods=['GET'])
def get_apps():
    return open_apps_data()


@server.route('/apps', methods=['POST'])
def post_apps():
    data = request.json
    apps = open_apps_data()

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

    save_apps(apps)

    return jsonify({
        "id": gen_id,
        "message": "Application ajoutée avec succès"
    }), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
def get_app(app_id):
    apps = open_apps_data()
    app = apps.get(app_id)
    if app:
        return jsonify(app)

    return jsonify({
        "message": "Pas d'application avec cet ID"
    }), 404


@server.route('/apps/<string:app_id>', methods=['DELETE'])
def delete_app(app_id):
    apps = open_apps_data()
    if app_id not in open_apps_data():
        return jsonify({"message": "Application non trouvée"}), 404

    apps.pop(app_id)
    save_apps(apps)
    return jsonify({
        "id": app_id,
        "message": "Application supprimée avec succès"
    }), 201


@server.route('/apps/<string:app_id>', methods=['PATCH'])
def patch_app(app_id):
    apps = open_apps_data()
    if app_id not in apps:
        return jsonify({"message": "Non trouvé"}), 404

    data = request.json
    apps[app_id].update({
        "name": data.get('name', apps[app_id]['name']),
        "description": data.get('description', apps[app_id]['description']),
        "repositoryUrl": data.get('repositoryUrl', apps[app_id]['repositoryUrl']),
        "ownerId": data.get('ownerId', apps[app_id]['ownerId']),
        "latestVersion": data.get('latestVersion', apps[app_id]['latestVersion']),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    })

    save_apps(apps)
    return jsonify({
        "id": app_id,
        "message": "Application modifiée",
        "app": apps[app_id]
    }), 200

@server.route('/apps/<string:app_id>/versions', methods=['GET'])
def get_versions(app_id):
    apps = open_apps_data()

@server.route('/apps/<string:app_id>/versions', methods=['POST'])
def post_versions(app_id):
    data = request.json

@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['GET'])
def get_version(app_id, version_id):
    apps = open_apps_data()

@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['PATCH'])
def patch_version(app_id, version_id):
    apps = open_apps_data()

@server.route('/apps/<string:app_id>/versions/<string:version_id>', methods=['DELETE'])
def delete_version(app_id, version_id):
    apps = open_apps_data()


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5001, debug=True)
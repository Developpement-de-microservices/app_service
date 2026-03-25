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


@server.route('/apps', methods=['GET'])
def get_apps():
    return open_apps_data()


@server.route('/apps', methods=['POST'])
def post_apps():
    data = request.json
    apps = open_apps_data()

    if not apps:
        new_id = 1
    else:
        reserved_ids = [int(k) for k in apps.keys()]
        new_id = max(reserved_ids) + 1

    str_id = str(new_id)

    apps[str_id] = {
        "name": data.get('name', 'N/A'),
        "description": data.get('description', 'N/A')
    }

    save_apps(apps)

    return jsonify({
        "id": new_id,
        "message": "Point d'accès ajouté avec succès"
    }), 201


@server.route('/apps/<string:app_id>', methods=['GET'])
def get_app(app_id):
    apps = open_apps_data()
    app = apps.get(app_id)
    if app:
        return jsonify({
            "id": app_id,
            "name": app['name'],
        })

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


@server.route('/apps/<string:app_id>', methods=['PUT'])
def put_app(app_id):
    apps = open_apps_data()
    if app_id not in apps:
        return jsonify({"message": "Non trouvé"}), 404

    data = request.json
    apps[app_id].update({
        "name": data.get('name', apps[app_id]['name']),
        "description": data.get('description', apps[app_id]['description'])
    })

    save_apps(apps)
    return jsonify({
        "id": app_id,
        "message": "Point d'accès modifié",
        "app": apps[app_id]
    }), 200


if __name__ == '__main__':
    server.run(host='0.0.0.0', port=5000, debug=True)
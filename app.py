from flask import Flask
import os
import json

app = Flask(__name__)

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

@app.route('/apps', methods=['GET'])
def get_apps():
    return open_apps_data()

@app.route('/apps', methods=['POST'])
def post_apps():
    data = request.json
    apps = open_apps_data()

    if not apps:
        new_id = 1
    else:
        ids_existants = [int(k) for k in apps.keys()]
        new_id = max(ids_existants) + 1
    
    str_id = str(new_id)
    
    apps[str_id] = {
        "name": data.get('name', 'N/A'),
        "description": data.get('description', 'N/A')
    }
    
    save_aps(aps)
    
    return jsonify({
        "id": new_id, 
        "message": "Point d'accès ajouté avec succès"
    }), 201

@app.route('/apps/<string:appId>', methods=['GET'])
def get_app(appId):
    return "Hello world"

@app.route('/apps/<appId>', methods=['DELETE'])
def delete_app():
    return

@app.route('/apps/<string:appId>', methods=['PUT'])
def put_app(appId):
    apps = open_apps_data()
    if appId not in apps:
        return jsonify({"message": "Non trouvé"}), 404
    
    data = request.json
    apps[appId].update({
        "name": data.get('name', apps[appId]['name']),
        "description": data.get('description', apps[appId]['description'])
    })
    
    save_aps(aps)
    return jsonify({"message": "Point d'accès modifié"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
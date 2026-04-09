"""
backend/app.py — Serveur Python optionnel pour Project Brain
Utilisé pour le parsing de fichiers Litematica (.litematic)
et les calculs plus complexes.

Installation : pip install flask flask-cors nbtlib
Lancement    : python app.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # Autorise les requêtes depuis le frontend

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


@app.route('/api/health')
def health():
    """Vérifie que le backend est en ligne."""
    return jsonify({'status': 'ok', 'version': '0.1.0'})


@app.route('/api/blocks')
def get_blocks():
    """Retourne la base de données des blocs."""
    try:
        with open(os.path.join(DATA_DIR, 'blocks.json'), 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/farms')
def get_farms():
    """Retourne la base de données des farms."""
    try:
        with open(os.path.join(DATA_DIR, 'farms.json'), 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/calculate/farm', methods=['POST'])
def calculate_farm():
    """
    Calcule le rendement d'une farm.
    Body JSON :
      { "farm_id": "iron_farm_standard", "tps": 18, "goal": 500000 }
    """
    data = request.get_json()
    farm_id = data.get('farm_id')
    tps = float(data.get('tps', 20))
    goal = int(data.get('goal', 0))

    with open(os.path.join(DATA_DIR, 'farms.json'), 'r', encoding='utf-8') as f:
        farms = json.load(f)

    farm = next((f for f in farms if f['id'] == farm_id), None)
    if not farm:
        return jsonify({'error': 'Farm non trouvée'}), 404

    rates = farm['rates']
    tps_loss = (20 - tps) * rates['per_tps_loss']
    brut = rates['base_per_hour']
    reel = max(0, brut - tps_loss)
    heures = (goal / reel) if reel > 0 and goal > 0 else None

    return jsonify({
        'farm': farm['name'],
        'brut_per_hour': brut,
        'reel_per_hour': reel,
        'min_sim_distance': rates['min_sim_distance'],
        'hours_to_goal': heures
    })


@app.route('/api/parse/litematic', methods=['POST'])
def parse_litematic():
    """
    Parse un fichier .litematic et retourne la liste des blocs.
    Nécessite : pip install nbtlib
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']

    try:
        import nbtlib
        from io import BytesIO

        nbt_data = nbtlib.load(BytesIO(file.read()))
        # Le format Litematica stocke les blocs dans Regions > <nom> > BlockStatePalette
        blocks = {}
        regions = nbt_data.get('Regions', {})

        for region_name, region in regions.items():
            palette = region.get('BlockStatePalette', [])
            for entry in palette:
                block_id = str(entry.get('Name', ''))
                if block_id and block_id != 'minecraft:air':
                    blocks[block_id] = blocks.get(block_id, 0) + 1

        return jsonify({
            'success': True,
            'blocks': [{'id': k, 'count': v} for k, v in blocks.items()],
            'total_blocks': sum(blocks.values())
        })

    except ImportError:
        return jsonify({
            'error': 'nbtlib non installé. Exécuter : pip install nbtlib'
        }), 500
    except Exception as e:
        return jsonify({'error': f'Erreur de parsing : {str(e)}'}), 500


if __name__ == '__main__':
    print('🧠 Project Brain Backend démarré sur http://localhost:5000')
    app.run(debug=True, port=5000)

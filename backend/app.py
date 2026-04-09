"""
backend/app.py — Serveur Python pour Project Brain
Gère le parsing Litematica et les calculs de ressources

Installation : pip install flask flask-cors nbtlib
Lancement    : python app.py
"""

import json
import math
from collections import Counter
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Charger le parser Litematica
try:
    from parser.litematica import LitematicaParser, LitematicaParseError
    litematica_parser = LitematicaParser(blocks_db_path=str(DATA_DIR / "blocks.json"))
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("[WARN] nbtlib manquant — pip install nbtlib")


# ==========================================
# UTILITAIRES
# ==========================================

def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def err(msg, code=400):
    return jsonify({"error": msg, "success": False}), code

def ok(data):
    return jsonify({"success": True, **data})

def format_hours(hours):
    if hours < 1/60: return "< 1 min"
    if hours < 1: return f"{int(hours*60)} min"
    if hours < 24:
        h, m = int(hours), int((hours % 1) * 60)
        return f"{h}h{m:02d}"
    return f"{int(hours//24)}j {int(hours%24)}h"


# ==========================================
# SYSTÈME
# ==========================================

@app.route("/api/health")
def health():
    blocks = load_json("blocks.json") if (DATA_DIR / "blocks.json").exists() else []
    farms  = load_json("farms.json")  if (DATA_DIR / "farms.json").exists()  else []
    return ok({
        "version": "0.1.0",
        "parser_available": PARSER_AVAILABLE,
        "blocks_count": len(blocks),
        "farms_count": len(farms),
    })


# ==========================================
# DONNÉES
# ==========================================

@app.route("/api/blocks")
def get_blocks():
    try:
        blocks = load_json("blocks.json")
        cat   = request.args.get("category")
        query = request.args.get("q", "").lower()
        raw   = request.args.get("raw")
        if cat:   blocks = [b for b in blocks if b.get("category") == cat]
        if raw:   blocks = [b for b in blocks if str(b.get("raw", False)).lower() == raw]
        if query: blocks = [b for b in blocks if
                            query in b.get("name","").lower() or
                            query in b.get("name_fr","").lower() or
                            query in b.get("id","").lower()]
        return ok({"blocks": blocks, "count": len(blocks)})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/farms")
def get_farms():
    try:
        farms = load_json("farms.json")
        cat   = request.args.get("category")
        diff  = request.args.get("difficulty")
        nether = request.args.get("nether")
        if cat:    farms = [f for f in farms if f.get("category") == cat]
        if diff:   farms = [f for f in farms if f.get("difficulty") == diff]
        if nether: farms = [f for f in farms if f.get("requires_nether", False) == (nether == "true")]
        return ok({"farms": farms, "count": len(farms)})
    except Exception as e:
        return err(str(e), 500)


# ==========================================
# CALCULS
# ==========================================

@app.route("/api/calculate/farm", methods=["POST"])
def calculate_farm():
    """Calcule le rendement réel d'une farm selon les paramètres serveur."""
    data = request.get_json(silent=True) or {}
    farm_id = data.get("farm_id")
    tps = float(data.get("tps", 20))
    goal = int(data.get("goal", 0))

    if not farm_id: return err("farm_id requis")

    try:
        farms = load_json("farms.json")
    except Exception as e:
        return err(str(e), 500)

    farm = next((f for f in farms if f["id"] == farm_id), None)
    if not farm: return err(f"Farm non trouvée : {farm_id}", 404)

    rates = farm.get("rates", {})
    brut  = rates.get("base_per_hour", 0)
    reel  = max(0, brut - (20 - tps) * rates.get("per_tps_loss", 0))
    eff   = round(reel / max(brut, 1) * 100, 1)
    hours = (goal / reel) if (goal > 0 and reel > 0) else None

    return ok({
        "farm": farm,
        "brut_per_hour": int(brut),
        "reel_per_hour": int(reel),
        "efficiency_pct": eff,
        "min_sim_distance": rates.get("min_sim_distance", 4),
        "hours_to_goal": round(hours, 2) if hours else None,
        "formatted_time": format_hours(hours) if hours else None,
    })


@app.route("/api/calculate/resources", methods=["POST"])
def calculate_resources():
    """Décompose un objectif en ressources brutes à farmer."""
    data = request.get_json(silent=True) or {}
    item_id  = data.get("item_id", "")
    quantity = int(data.get("quantity", 0))

    if not item_id:   return err("item_id requis")
    if quantity <= 0: return err("quantity doit être > 0")
    if ":" not in item_id: item_id = f"minecraft:{item_id}"

    try:
        blocks_list = load_json("blocks.json")
        db = {b["id"]: b for b in blocks_list}
    except Exception as e:
        return err(str(e), 500)

    if item_id not in db:
        return err(f"Item non trouvé : {item_id}", 404)

    def resolve(bid, qty, depth=0):
        if depth > 10: return [{"id": bid, "name": bid, "quantity": qty, "step": "farmer", "depth": depth}]
        info = db.get(bid, {})
        name = info.get("name_fr") or info.get("name", bid)
        if not info or info.get("raw"):
            return [{"id": bid, "name": name, "quantity": qty, "step": "farmer", "depth": depth}]
        recipe = info.get("recipe")
        if not recipe:
            return [{"id": bid, "name": name, "quantity": qty, "step": "farmer", "depth": depth}]
        output = recipe.get("output", 1)
        batches = math.ceil(qty / max(output, 1))
        step = "fondre" if recipe.get("type") == "furnace" else "crafter"
        result = [{"id": bid, "name": name, "quantity": qty, "step": step, "depth": depth}]
        for ing in recipe.get("ingredients", []):
            result.extend(resolve(ing["id"], batches * ing.get("count", 1), depth + 1))
        return result

    decomp = resolve(item_id, quantity)
    raw_totals: Counter = Counter()
    for item in decomp:
        if item["step"] == "farmer":
            raw_totals[item["id"]] += item["quantity"]

    raw_list = []
    for rid, qty in sorted(raw_totals.items(), key=lambda x: x[1], reverse=True):
        info = db.get(rid, {})
        raw_list.append({
            "id": rid,
            "name": info.get("name_fr") or info.get("name", rid),
            "quantity": qty,
            "stacks": qty // 64,
            "remainder": qty % 64,
        })

    return ok({"item_id": item_id, "quantity": quantity,
               "decomposition": decomp, "raw_resources": raw_list})


# ==========================================
# LITEMATICA
# ==========================================

@app.route("/api/parse/litematic", methods=["POST"])
def parse_litematic():
    """
    Upload + parse d'un fichier .litematic.
    Form: file=<fichier>
    """
    if not PARSER_AVAILABLE:
        return err("Parser indisponible — installer nbtlib : pip install nbtlib", 503)
    if "file" not in request.files:
        return err("Champ 'file' requis (multipart/form-data)")

    f = request.files["file"]
    if not f.filename.lower().endswith((".litematic", ".schem")):
        return err("Extension invalide (.litematic ou .schem requis)")

    data = f.read()
    if not data:         return err("Fichier vide")
    if len(data) > 50_000_000: return err("Fichier trop volumineux (max 50 MB)")

    try:
        result = litematica_parser.parse_bytes(data)

        # Ajouter des suggestions de farms
        try:
            farms = load_json("farms.json")
            farm_map = {}
            for farm in farms:
                for oid in ([farm.get("output_item")] + farm.get("output_items", [])):
                    if oid and oid not in farm_map:
                        farm_map[oid] = farm
            suggestions = []
            for res in result.get("raw_resources", [])[:8]:
                farm = farm_map.get(res["id"])
                if farm:
                    reel = farm["rates"].get("base_per_hour", 0)
                    qty  = res["quantity"]
                    hrs  = qty / reel if reel > 0 else None
                    suggestions.append({
                        "resource_id":   res["id"],
                        "resource_name": res.get("name", ""),
                        "quantity":      qty,
                        "farm_id":       farm["id"],
                        "farm_name":     farm["name"],
                        "farm_rate":     reel,
                        "formatted_time": format_hours(hrs) if hrs else None,
                    })
            result["farm_suggestions"] = suggestions
        except Exception:
            result["farm_suggestions"] = []

        return ok(result)

    except LitematicaParseError as e:
        return err(str(e))
    except Exception as e:
        return err(f"Erreur interne : {e}", 500)


# ==========================================
# LANCEMENT
# ==========================================

if __name__ == "__main__":
    print("=" * 50)
    print("  🧠 Project Brain Backend  v0.1.0")
    print(f"  Parser  : {'✓ nbtlib disponible' if PARSER_AVAILABLE else '✗ pip install nbtlib'}")
    print(f"  Données : {DATA_DIR}")
    print("  URL     : http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000, host="0.0.0.0")

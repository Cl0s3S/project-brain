"""
backend/parser/litematica.py
Parser complet pour les fichiers .litematic (format Litematica Mod)

Format : fichier NBT compressé en gzip
Structure :
  root
  ├── Metadata
  │   ├── Name, Author, TimeCreated, TimeModified
  │   ├── RegionCount
  │   └── EnclosingSize (x, y, z)
  └── Regions
      └── <nom_région>
          ├── BlockStatePalette  ← liste des types de blocs
          ├── BlockStates        ← bitarray compressé des positions
          ├── Size               ← dimensions (x, y, z)
          └── TileEntities, Entities

Dépendances : pip install nbtlib
"""

import json
import math
import struct
from pathlib import Path
from collections import Counter
from typing import Dict, List, Optional, Tuple

try:
    import nbtlib
    NBTLIB_AVAILABLE = True
except ImportError:
    NBTLIB_AVAILABLE = False


class LitematicaParseError(Exception):
    """Erreur de parsing d'un fichier Litematica."""
    pass


class LitematicaParser:
    """
    Parse un fichier .litematic et extrait :
      - Les métadonnées (nom, auteur, dimensions)
      - La liste des blocs avec quantités
      - La décomposition en ressources brutes (via blocks.json)
    """

    def __init__(self, blocks_db_path: Optional[str] = None):
        """
        Args:
            blocks_db_path: Chemin vers le fichier blocks.json.
                            Si None, utilise le chemin par défaut du projet.
        """
        if not NBTLIB_AVAILABLE:
            raise LitematicaParseError(
                "nbtlib n'est pas installé. Exécuter : pip install nbtlib"
            )

        self.blocks_db: Dict = {}
        if blocks_db_path:
            self._load_blocks_db(blocks_db_path)
        else:
            # Chemin par défaut relatif à ce fichier
            default_path = Path(__file__).parent.parent.parent / "data" / "blocks.json"
            if default_path.exists():
                self._load_blocks_db(str(default_path))

    def _load_blocks_db(self, path: str) -> None:
        """Charge la base de données des blocs depuis blocks.json."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                blocks_list = json.load(f)
                self.blocks_db = {b["id"]: b for b in blocks_list}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[WARN] Impossible de charger blocks.json : {e}")

    def parse_file(self, filepath: str) -> Dict:
        """
        Parse un fichier .litematic et retourne un dictionnaire complet.

        Args:
            filepath: Chemin vers le fichier .litematic

        Returns:
            {
                "metadata": {...},
                "blocks": [{"id": ..., "name": ..., "count": ...}, ...],
                "total_blocks": int,
                "raw_resources": [...],   # ressources brutes nécessaires
                "volume": int,            # volume total de la structure
                "dimensions": {"x": int, "y": int, "z": int}
            }

        Raises:
            LitematicaParseError: Si le fichier est invalide ou corrompu
        """
        path = Path(filepath)
        if not path.exists():
            raise LitematicaParseError(f"Fichier introuvable : {filepath}")
        if path.suffix not in (".litematic", ".schem"):
            raise LitematicaParseError(
                f"Extension non supportée : {path.suffix}. "
                "Utiliser .litematic ou .schem"
            )

        try:
            nbt_data = nbtlib.load(filepath)
        except Exception as e:
            raise LitematicaParseError(f"Erreur de lecture NBT : {e}")

        try:
            return self._extract_data(nbt_data)
        except Exception as e:
            raise LitematicaParseError(f"Erreur d'extraction des données : {e}")

    def parse_bytes(self, data: bytes) -> Dict:
        """
        Parse des données .litematic depuis un objet bytes (ex: upload Flask).

        Args:
            data: Contenu du fichier en bytes

        Returns:
            Même structure que parse_file()
        """
        import io
        try:
            nbt_data = nbtlib.load(io.BytesIO(data))
        except Exception as e:
            raise LitematicaParseError(f"Erreur de lecture NBT : {e}")

        try:
            return self._extract_data(nbt_data)
        except Exception as e:
            raise LitematicaParseError(f"Erreur d'extraction des données : {e}")

    def _extract_data(self, nbt_data) -> Dict:
        """Extrait toutes les données depuis le NBT parsé."""
        metadata = self._extract_metadata(nbt_data)
        block_counts = self._extract_blocks(nbt_data)
        dimensions = self._extract_dimensions(nbt_data)

        # Filtrer l'air et trier par quantité décroissante
        filtered = {
            k: v for k, v in block_counts.items()
            if k not in ("minecraft:air", "minecraft:cave_air", "minecraft:void_air")
        }
        sorted_blocks = sorted(filtered.items(), key=lambda x: x[1], reverse=True)

        # Construire la liste des blocs avec métadonnées
        blocks_list = []
        for block_id, count in sorted_blocks:
            info = self.blocks_db.get(block_id, {})
            blocks_list.append({
                "id": block_id,
                "name": info.get("name", block_id.replace("minecraft:", "").replace("_", " ").title()),
                "name_fr": info.get("name_fr", ""),
                "count": count,
                "category": info.get("category", "unknown"),
                "craftable": info.get("craftable", False),
                "raw": info.get("raw", False)
            })

        total_blocks = sum(count for _, count in sorted_blocks)
        volume = dimensions["x"] * dimensions["y"] * dimensions["z"]

        # Calculer les ressources brutes
        raw_resources = self._compute_raw_resources(filtered)

        return {
            "metadata": metadata,
            "blocks": blocks_list,
            "total_blocks": total_blocks,
            "air_blocks": block_counts.get("minecraft:air", 0),
            "volume": volume,
            "fill_ratio": round(total_blocks / max(volume, 1) * 100, 1),
            "dimensions": dimensions,
            "raw_resources": raw_resources,
            "unknown_blocks": [
                b["id"] for b in blocks_list if b["category"] == "unknown"
            ]
        }

    def _extract_metadata(self, nbt_data) -> Dict:
        """Extrait les métadonnées du fichier."""
        metadata = {}
        try:
            meta = nbt_data.get("Metadata", {})
            metadata["name"] = str(meta.get("Name", "Sans nom"))
            metadata["author"] = str(meta.get("Author", "Inconnu"))
            metadata["description"] = str(meta.get("Description", ""))
            metadata["region_count"] = int(meta.get("RegionCount", 1))
            metadata["time_created"] = int(meta.get("TimeCreated", 0))
            metadata["time_modified"] = int(meta.get("TimeModified", 0))

            enclosing = meta.get("EnclosingSize", {})
            metadata["enclosing_size"] = {
                "x": int(enclosing.get("x", 0)),
                "y": int(enclosing.get("y", 0)),
                "z": int(enclosing.get("z", 0))
            }
        except Exception:
            pass
        return metadata

    def _extract_dimensions(self, nbt_data) -> Dict:
        """Extrait les dimensions totales du schéma."""
        total_x, total_y, total_z = 0, 0, 0
        try:
            regions = nbt_data.get("Regions", {})
            for region in regions.values():
                size = region.get("Size", {})
                total_x = max(total_x, abs(int(size.get("x", 0))))
                total_y = max(total_y, abs(int(size.get("y", 0))))
                total_z = max(total_z, abs(int(size.get("z", 0))))
        except Exception:
            pass
        return {"x": total_x, "y": total_y, "z": total_z}

    def _extract_blocks(self, nbt_data) -> Counter:
        """
        Extrait et compte tous les blocs du fichier NBT.

        Gère le format bitarray compact de Litematica :
        Les positions des blocs sont stockées dans un long[] compressé.
        Chaque entrée palette prend ceil(log2(palette_size)) bits.
        """
        total_counts: Counter = Counter()

        regions = nbt_data.get("Regions", {})
        if not regions:
            raise LitematicaParseError("Aucune région trouvée dans le fichier")

        for region_name, region in regions.items():
            try:
                counts = self._extract_region_blocks(region, str(region_name))
                total_counts.update(counts)
            except Exception as e:
                print(f"[WARN] Erreur région '{region_name}': {e}")
                # Fallback : compter juste la palette (approximatif)
                palette = region.get("BlockStatePalette", [])
                for entry in palette:
                    block_id = str(entry.get("Name", "minecraft:air"))
                    if block_id != "minecraft:air":
                        total_counts[block_id] += 1

        return total_counts

    def _extract_region_blocks(self, region, region_name: str) -> Counter:
        """
        Extrait les blocs d'une région en décodant le bitarray.
        """
        palette = region.get("BlockStatePalette", [])
        block_states = region.get("BlockStates", None)
        size = region.get("Size", {})

        if not palette:
            return Counter()

        size_x = abs(int(size.get("x", 0)))
        size_y = abs(int(size.get("y", 0)))
        size_z = abs(int(size.get("z", 0)))
        volume = size_x * size_y * size_z

        if volume == 0:
            return Counter()

        # Nombre de bits par bloc dans le bitarray
        palette_size = len(palette)
        if palette_size <= 1:
            # Un seul type de bloc dans cette région
            block_id = str(palette[0].get("Name", "minecraft:air"))
            return Counter({block_id: volume})

        bits_per_block = max(2, math.ceil(math.log2(palette_size)))

        # Compter par palette si pas de BlockStates disponible
        if block_states is None:
            counts = Counter()
            for entry in palette:
                block_id = str(entry.get("Name", "minecraft:air"))
                counts[block_id] += 1
            return counts

        # Décoder le bitarray compact
        try:
            counts = self._decode_bitarray(block_states, bits_per_block, volume, palette)
            return counts
        except Exception as e:
            print(f"[WARN] Erreur décodage bitarray région '{region_name}': {e}")
            # Fallback : estimation par palette avec répartition égale
            counts = Counter()
            per_type = max(1, volume // palette_size)
            for entry in palette:
                block_id = str(entry.get("Name", "minecraft:air"))
                counts[block_id] += per_type
            return counts

    def _decode_bitarray(self, block_states, bits_per_block: int, volume: int, palette) -> Counter:
        """
        Décode le bitarray compact du format Litematica.

        Le format Litematica utilise des long[] (int64) pour stocker les indices de palette.
        Chaque long contient floor(64 / bits_per_block) indices.
        Les bits d'un bloc ne traversent PAS les frontières de long (padding si nécessaire).
        """
        counts = Counter()

        # Extraire les valeurs long[]
        longs = []
        try:
            for val in block_states:
                # nbtlib retourne des LongArray
                longs.append(int(val))
        except TypeError:
            # Peut être un seul entier
            longs = [int(block_states)]

        if not longs:
            return counts

        mask = (1 << bits_per_block) - 1
        indices_per_long = 64 // bits_per_block
        block_index = 0

        for long_val in longs:
            if block_index >= volume:
                break
            # Les long Minecraft sont signés — convertir en non signé
            if long_val < 0:
                long_val += (1 << 64)

            for i in range(indices_per_long):
                if block_index >= volume:
                    break
                palette_idx = (long_val >> (i * bits_per_block)) & mask
                if palette_idx < len(palette):
                    block_id = str(palette[palette_idx].get("Name", "minecraft:air"))
                    counts[block_id] += 1
                block_index += 1

        return counts

    def _compute_raw_resources(self, block_counts: Dict) -> List[Dict]:
        """
        Calcule les ressources brutes nécessaires en décomposant les recettes.
        Résout récursivement jusqu'aux matériaux de base.

        Returns:
            Liste triée de ressources brutes avec quantités totales
        """
        if not self.blocks_db:
            return []

        raw_totals: Counter = Counter()

        for block_id, count in block_counts.items():
            self._resolve_to_raw(block_id, count, raw_totals, depth=0)

        # Construire la liste finale
        result = []
        for item_id, qty in sorted(raw_totals.items(), key=lambda x: x[1], reverse=True):
            info = self.blocks_db.get(item_id, {})
            result.append({
                "id": item_id,
                "name": info.get("name", item_id.replace("minecraft:", "").title()),
                "name_fr": info.get("name_fr", ""),
                "quantity": qty,
                "category": info.get("category", "unknown")
            })

        return result

    def _resolve_to_raw(self, block_id: str, count: int, accumulator: Counter, depth: int) -> None:
        """
        Résolution récursive : décompose un bloc en ses matériaux bruts.
        Limite la profondeur à 10 pour éviter les boucles infinies.
        """
        if depth > 10:
            accumulator[block_id] += count
            return

        info = self.blocks_db.get(block_id)

        # Bloc inconnu ou matière première → on l'ajoute tel quel
        if not info or info.get("raw", False):
            accumulator[block_id] += count
            return

        recipe = info.get("recipe")
        if not recipe:
            # Craftable mais pas de recette connue → matière première approximative
            accumulator[block_id] += count
            return

        ingredients = recipe.get("ingredients", [])
        output_qty = recipe.get("output", 1)
        recipe_type = recipe.get("type", "crafting")

        # Nombre de fois qu'on doit crafter pour obtenir `count` items
        batches = math.ceil(count / max(output_qty, 1))

        if recipe_type == "furnace":
            # Pour les fours, on compte aussi le fuel (approximatif)
            fuel_cost = recipe.get("fuel_cost", 0.1)  # fuel par item
            # On n'ajoute pas le fuel dans les ressources brutes pour l'instant
            for ing in ingredients:
                ing_id = ing.get("id", "")
                ing_count = ing.get("count", 1)
                if ing_id:
                    self._resolve_to_raw(ing_id, batches * ing_count, accumulator, depth + 1)

        elif recipe_type == "smithing":
            for ing in ingredients:
                ing_id = ing.get("id", "")
                ing_count = ing.get("count", 1)
                if ing_id:
                    self._resolve_to_raw(ing_id, batches * ing_count, accumulator, depth + 1)

        else:
            # crafting (toutes variantes)
            for ing in ingredients:
                ing_id = ing.get("id", "")
                ing_count = ing.get("count", 1)
                if ing_id:
                    self._resolve_to_raw(ing_id, batches * ing_count, accumulator, depth + 1)


def format_result_report(result: Dict) -> str:
    """
    Génère un rapport texte lisible depuis le résultat du parser.

    Args:
        result: Dictionnaire retourné par LitematicaParser.parse_file()

    Returns:
        Rapport formaté en texte
    """
    meta = result.get("metadata", {})
    dims = result.get("dimensions", {})

    lines = [
        "=" * 60,
        f"  PROJET : {meta.get('name', 'Inconnu')}",
        f"  Auteur : {meta.get('author', 'Inconnu')}",
        "=" * 60,
        f"  Dimensions : {dims.get('x', 0)} × {dims.get('y', 0)} × {dims.get('z', 0)} blocs",
        f"  Volume total : {result.get('volume', 0):,} blocs",
        f"  Blocs posés  : {result.get('total_blocks', 0):,} ({result.get('fill_ratio', 0)}% rempli)",
        "",
        "  BLOCS NÉCESSAIRES :",
        "-" * 60
    ]

    for block in result.get("blocks", []):
        stacks = block["count"] // 64
        remainder = block["count"] % 64
        stack_str = f"{stacks} stacks" + (f" + {remainder}" if remainder else "")
        name = block.get("name_fr") or block.get("name") or block["id"]
        lines.append(
            f"  {name:<35} {block['count']:>8,}  ({stack_str})"
        )

    if result.get("raw_resources"):
        lines += [
            "",
            "  RESSOURCES BRUTES À FARMER :",
            "-" * 60
        ]
        for res in result.get("raw_resources", []):
            stacks = res["quantity"] // 64
            name = res.get("name_fr") or res.get("name") or res["id"]
            lines.append(
                f"  {name:<35} {res['quantity']:>8,}  ({stacks} stacks)"
            )

    if result.get("unknown_blocks"):
        lines += [
            "",
            f"  ⚠ Blocs non reconnus ({len(result['unknown_blocks'])}) :",
            "  " + ", ".join(result["unknown_blocks"][:10])
        ]

    lines.append("=" * 60)
    return "\n".join(lines)


# ==========================================
# UTILISATION EN LIGNE DE COMMANDE
# ==========================================
if __name__ == "__main__":
    import sys
    import argparse

    parser_args = argparse.ArgumentParser(
        description="Parser de fichiers .litematic — Project Brain"
    )
    parser_args.add_argument("filepath", help="Chemin vers le fichier .litematic")
    parser_args.add_argument(
        "--json", action="store_true",
        help="Sortie en JSON (par défaut : rapport texte)"
    )
    parser_args.add_argument(
        "--blocks-db", default=None,
        help="Chemin vers blocks.json (optionnel)"
    )
    parser_args.add_argument(
        "--output", default=None,
        help="Fichier de sortie (optionnel, sinon stdout)"
    )

    args = parser_args.parse_args()

    try:
        lm_parser = LitematicaParser(blocks_db_path=args.blocks_db)
        result = lm_parser.parse_file(args.filepath)

        if args.json:
            output = json.dumps(result, ensure_ascii=False, indent=2)
        else:
            output = format_result_report(result)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Résultat sauvegardé dans : {args.output}")
        else:
            print(output)

    except LitematicaParseError as e:
        print(f"ERREUR : {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)

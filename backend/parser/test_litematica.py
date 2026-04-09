"""
backend/parser/test_litematica.py
Tests unitaires pour le parser Litematica

Lancement : python -m pytest test_litematica.py -v
         OU python test_litematica.py
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ajouter le parent au path pour l'import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ==========================================
# MOCK nbtlib pour les tests sans dépendance
# ==========================================
class MockNBT(dict):
    pass


def make_mock_nbt(name="Test Build", author="TestPlayer",
                  region_blocks=None, size=(10, 5, 10)):
    """Crée un faux NBT pour les tests."""
    if region_blocks is None:
        region_blocks = {"minecraft:stone_bricks": 200, "minecraft:oak_planks": 50}

    mock = MockNBT()
    mock["Metadata"] = {
        "Name": name,
        "Author": author,
        "Description": "Test schematic",
        "RegionCount": 1,
        "TimeCreated": 1700000000,
        "TimeModified": 1700000000,
        "EnclosingSize": {"x": size[0], "y": size[1], "z": size[2]}
    }

    # Palette : liste des blocs
    palette = []
    for block_id in region_blocks:
        palette.append({"Name": block_id, "Properties": {}})

    mock["Regions"] = {
        "Main": {
            "BlockStatePalette": palette,
            "BlockStates": None,  # On bypasse le décodage bitarray dans les tests
            "Size": {"x": size[0], "y": size[1], "z": size[2]},
            "TileEntities": [],
            "Entities": []
        }
    }
    return mock


# ==========================================
# Tests
# ==========================================

def test_import():
    """Test que le module s'importe correctement."""
    try:
        from backend.parser.litematica import LitematicaParser, LitematicaParseError, format_result_report
        print("✓ Import OK")
        return True
    except ImportError as e:
        print(f"✗ Import échoué : {e}")
        return False


def test_blocks_db_loading():
    """Test le chargement de la base de données des blocs."""
    try:
        from backend.parser.litematica import LitematicaParser
        db_path = str(Path(__file__).parent.parent.parent / "data" / "blocks.json")

        if not Path(db_path).exists():
            print(f"⚠ blocks.json non trouvé à {db_path}, test ignoré")
            return True

        parser = LitematicaParser(blocks_db_path=db_path)
        assert len(parser.blocks_db) > 0, "La DB ne devrait pas être vide"
        assert "minecraft:stone_bricks" in parser.blocks_db, "stone_bricks devrait être dans la DB"
        assert "minecraft:iron_ingot" in parser.blocks_db, "iron_ingot devrait être dans la DB"
        print(f"✓ Base de données chargée ({len(parser.blocks_db)} blocs)")
        return True
    except Exception as e:
        print(f"✗ Erreur chargement DB : {e}")
        return False


def test_metadata_extraction():
    """Test l'extraction des métadonnées."""
    try:
        from backend.parser.litematica import LitematicaParser
        parser = LitematicaParser()

        mock_nbt = make_mock_nbt(name="Mon Château", author="Steve")
        metadata = parser._extract_metadata(mock_nbt)

        assert metadata["name"] == "Mon Château", f"Nom incorrect : {metadata['name']}"
        assert metadata["author"] == "Steve", f"Auteur incorrect : {metadata['author']}"
        assert metadata["region_count"] == 1, "RegionCount devrait être 1"
        print("✓ Extraction métadonnées OK")
        return True
    except Exception as e:
        print(f"✗ Erreur extraction métadonnées : {e}")
        return False


def test_dimensions_extraction():
    """Test l'extraction des dimensions."""
    try:
        from backend.parser.litematica import LitematicaParser
        parser = LitematicaParser()

        mock_nbt = make_mock_nbt(size=(32, 16, 48))
        dims = parser._extract_dimensions(mock_nbt)

        assert dims["x"] == 32, f"X incorrect : {dims['x']}"
        assert dims["y"] == 16, f"Y incorrect : {dims['y']}"
        assert dims["z"] == 48, f"Z incorrect : {dims['z']}"
        print("✓ Extraction dimensions OK")
        return True
    except Exception as e:
        print(f"✗ Erreur extraction dimensions : {e}")
        return False


def test_raw_resource_resolution_simple():
    """Test la décomposition en ressources brutes — cas simple."""
    try:
        from backend.parser.litematica import LitematicaParser
        db_path = str(Path(__file__).parent.parent.parent / "data" / "blocks.json")

        if not Path(db_path).exists():
            print("⚠ blocks.json non trouvé, test ignoré")
            return True

        parser = LitematicaParser(blocks_db_path=db_path)

        # 100 stone bricks = 100 stone = 100 cobblestone
        raw = Counter()
        parser._resolve_to_raw("minecraft:stone_bricks", 100, raw, depth=0)

        # stone_bricks → stone (4 bricks = 4 stone, recette 2x2 → output 4)
        # stone → cobblestone (1:1 au four)
        assert "minecraft:cobblestone" in raw, "cobblestone devrait être dans les ressources brutes"
        print(f"  stone_bricks×100 → {dict(raw)}")
        print("✓ Résolution ressources brutes (simple) OK")
        return True
    except Exception as e:
        print(f"✗ Erreur résolution ressources brutes : {e}")
        return False


def test_raw_resource_resolution_chain():
    """Test la décomposition en chaîne — ex: deepslate tiles."""
    try:
        from backend.parser.litematica import LitematicaParser
        db_path = str(Path(__file__).parent.parent.parent / "data" / "blocks.json")

        if not Path(db_path).exists():
            print("⚠ blocks.json non trouvé, test ignoré")
            return True

        parser = LitematicaParser(blocks_db_path=db_path)

        # deepslate_tiles → deepslate_bricks → polished_deepslate → cobbled_deepslate
        raw = Counter()
        parser._resolve_to_raw("minecraft:deepslate_tiles", 64, raw, depth=0)

        assert "minecraft:cobbled_deepslate" in raw, \
            "cobbled_deepslate devrait être dans les ressources brutes"
        print(f"  deepslate_tiles×64 → {dict(raw)}")
        print("✓ Résolution ressources brutes (chaîne) OK")
        return True
    except Exception as e:
        print(f"✗ Erreur résolution chaîne : {e}")
        return False


def test_bitarray_decoding():
    """Test le décodage du bitarray compact."""
    try:
        from backend.parser.litematica import LitematicaParser
        parser = LitematicaParser()

        # Palette de 4 blocs → 2 bits par bloc
        palette = [
            {"Name": "minecraft:air"},
            {"Name": "minecraft:stone"},
            {"Name": "minecraft:oak_planks"},
            {"Name": "minecraft:glass"}
        ]

        # On encode manuellement 16 blocs : 8 stones (idx=1), 4 planks (idx=2), 4 glass (idx=3)
        # bits_per_block = 2, indices_per_long = 32
        # Séquence : 1,1,1,1,1,1,1,1, 2,2,2,2, 3,3,3,3
        bits_per_block = 2
        long_val = 0
        sequence = [1]*8 + [2]*4 + [3]*4
        for i, idx in enumerate(sequence):
            long_val |= (idx << (i * bits_per_block))

        # nbtlib retourne des valeurs signées parfois
        counts = parser._decode_bitarray([long_val], bits_per_block, 16, palette)

        assert counts["minecraft:stone"] == 8, f"stone : {counts['minecraft:stone']} != 8"
        assert counts["minecraft:oak_planks"] == 4, f"oak_planks : {counts['minecraft:oak_planks']} != 4"
        assert counts["minecraft:glass"] == 4, f"glass : {counts['minecraft:glass']} != 4"
        print("✓ Décodage bitarray OK")
        return True
    except Exception as e:
        print(f"✗ Erreur décodage bitarray : {e}")
        import traceback
        traceback.print_exc()
        return False


def test_format_report():
    """Test la génération du rapport texte."""
    try:
        from backend.parser.litematica import format_result_report
        mock_result = {
            "metadata": {"name": "Test", "author": "Steve"},
            "dimensions": {"x": 10, "y": 5, "z": 10},
            "volume": 500,
            "total_blocks": 300,
            "fill_ratio": 60.0,
            "blocks": [
                {"id": "minecraft:stone_bricks", "name": "Stone Bricks", "name_fr": "Briques de pierre", "count": 200},
                {"id": "minecraft:oak_planks", "name": "Oak Planks", "name_fr": "Planches de chêne", "count": 100}
            ],
            "raw_resources": [
                {"id": "minecraft:cobblestone", "name": "Cobblestone", "name_fr": "Cobblestone", "quantity": 200}
            ],
            "unknown_blocks": []
        }

        report = format_result_report(mock_result)
        assert "Test" in report, "Le nom devrait être dans le rapport"
        assert "Stone Bricks" in report or "Briques de pierre" in report
        assert "Cobblestone" in report
        print("✓ Génération rapport OK")
        return True
    except Exception as e:
        print(f"✗ Erreur génération rapport : {e}")
        return False


def test_file_not_found():
    """Test la gestion d'un fichier inexistant."""
    try:
        from backend.parser.litematica import LitematicaParser, LitematicaParseError
        parser = LitematicaParser()
        try:
            parser.parse_file("/chemin/inexistant/fichier.litematic")
            print("✗ Devrait lever une LitematicaParseError")
            return False
        except LitematicaParseError:
            print("✓ Gestion fichier inexistant OK")
            return True
    except Exception as e:
        print(f"✗ Erreur inattendue : {e}")
        return False


def test_wrong_extension():
    """Test la gestion d'une mauvaise extension."""
    try:
        import tempfile, os
        from backend.parser.litematica import LitematicaParser, LitematicaParseError

        # Créer un fichier temporaire avec mauvaise extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"dummy")
            tmp_path = f.name

        parser = LitematicaParser()
        try:
            parser.parse_file(tmp_path)
            print("✗ Devrait lever une LitematicaParseError pour .txt")
            return False
        except LitematicaParseError:
            print("✓ Gestion mauvaise extension OK")
            return True
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        print(f"✗ Erreur inattendue : {e}")
        return False


# ==========================================
# RUNNER
# ==========================================
if __name__ == "__main__":
    tests = [
        test_import,
        test_blocks_db_loading,
        test_metadata_extraction,
        test_dimensions_extraction,
        test_raw_resource_resolution_simple,
        test_raw_resource_resolution_chain,
        test_bitarray_decoding,
        test_format_report,
        test_file_not_found,
        test_wrong_extension,
    ]

    passed = 0
    failed = 0
    print("\n" + "="*60)
    print("  TESTS — Parser Litematica")
    print("="*60 + "\n")

    for test in tests:
        print(f"  [{test.__name__}]")
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ Exception non gérée : {e}")
            failed += 1
        print()

    print("="*60)
    print(f"  Résultat : {passed} réussis / {failed} échoués / {len(tests)} total")
    print("="*60 + "\n")

    sys.exit(0 if failed == 0 else 1)

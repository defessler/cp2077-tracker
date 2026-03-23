#!/usr/bin/env python3
"""
read_inventory.py  ·  CP2077 Save Inventory Reader
===================================================
Reads the binary sav.dat to extract iconic weapon inventory.
Uses CyberpunkPythonHacks to parse the node tree, then scans the
inventory node for TweakDB item hashes (CRC32 of original-case string).
Maps found Items.* TweakDB IDs to the tracker's _weapon_* pseudo-IDs.

Requires: CyberpunkPythonHacks in tools/CyberpunkPythonHacks/
          TweakDBIDs.json in tools/TweakDBIDs.json
Run:      python -X utf8 read_inventory.py [save_folder_name]

Output:
  - Prints which tracked iconic weapons are in inventory
  - Writes  tracker_weapons.json  (used by tracker_local.py if present)
"""

from __future__ import annotations
import binascii, json, struct, sys
from datetime import datetime
from pathlib import Path

HERE      = Path(__file__).parent
SAVE_ROOT = Path(r"C:\Users\defes\Saved Games\CD Projekt Red\Cyberpunk 2077")
TOOLS_DIR = HERE / "tools"

# ── TweakDB ID → _weapon_* pseudo-ID mapping ──────────────────────────────────
TWEAKDB_TO_WEAPON: dict[str, str] = {
    # Open-world / purchasable
    "Items.DyingNightMQ006":        "_weapon_dying_night",
    "Items.Preset_Militech_Guts":   "_weapon_guts",
    "Items.Preset_Knife_Stout":     "_weapon_guts",
    "Items.Preset_Base_Copperhead": "_weapon_blue_fang",
    "Items.Preset_Knife_Military":  "_weapon_headhunter",
    "Items.mq007_skippy":           "_weapon_skippy",
    "Items.Preset_Burya_Default":   "_weapon_comrades_hammer",
    "Items.Preset_Burya_Pimp":      "_weapon_comrades_hammer",
    # Act 1
    "Items.Preset_Kenshin_Spy":     "_weapon_kongou",
    "Items.Preset_Katana_Saburo":   "_weapon_satori",
    "Items.Preset_Kenshin_Royce":   "_weapon_chaos",
    "Items.Preset_Saratoga_Maelstrom": "_weapon_buzzsaw",
    # Act 2
    "Items.Preset_Liberty_Dex":     "_weapon_plan_b",
    "Items.Preset_Katana_Cocktail": "_weapon_cocktail_stick",
    "Items.Preset_Dildo_Stout":     "_weapon_sir_john",
    "Items.Preset_Knife_Kurtz_1":   "_weapon_stinger",
    "Items.Preset_Saratoga_Raffen": "_weapon_fenrir",
    "Items.Preset_Guillotine_Default": "_weapon_guillotine",
    "Items.Preset_Katana_Surgeon":  "_weapon_scalpel",
    "Items.Preset_Achilles_Nash":   "_weapon_widow_maker",
    "Items.Preset_Kenshin_Frank":   "_weapon_problem_solver",
    "Items.Preset_Katana_E3":       "_weapon_byakko",
    "Items.Preset_Grad_AirDrop":    "_weapon_ofive",
    "Items.Preset_Tactician_Dino":  "_weapon_psalm",
    "Items.Preset_Grad_Panam":      "_weapon_overwatch",
    "Items.Preset_Saratoga_Arasaka_2077": "_weapon_ba_xing_chong",
    "Items.Preset_Overture_Dante":  "_weapon_amnesty",
    # Side jobs
    "Items.mq025_buck_gun":         "_weapon_crash",
    "Items.Preset_Satara_Brick":    "_weapon_bloody_maria",
    "Items.sq029_rivers_gun":       "_weapon_archangel",
    "Items.Preset_Omaha_Suzie":     "_weapon_breakthrough",
    "Items.Preset_Nue_Maiko":       "_weapon_mox",
    "Items.sq030_judy_romance":     "_weapon_pride",
    # Phantom Liberty
    "Items.Preset_Hercules_Prototype": "_weapon_erebus",
    "Items.Preset_Senkoh_Prototype":   "_weapon_hawk",
    "Items.Preset_Rasetsu_Prototype":  "_weapon_rasetsu",
}

TRACKED_WEAPONS = [
    "_weapon_dying_night", "_weapon_guts", "_weapon_blue_fang",
    "_weapon_headhunter", "_weapon_skippy", "_weapon_comrades_hammer",
    "_weapon_kongou", "_weapon_satori", "_weapon_chaos", "_weapon_buzzsaw",
    "_weapon_plan_b", "_weapon_cocktail_stick", "_weapon_sir_john",
    "_weapon_stinger", "_weapon_fenrir", "_weapon_guillotine",
    "_weapon_scalpel", "_weapon_widow_maker", "_weapon_problem_solver",
    "_weapon_byakko", "_weapon_ofive", "_weapon_psalm",
    "_weapon_overwatch", "_weapon_ba_xing_chong", "_weapon_amnesty",
    "_weapon_crash", "_weapon_bloody_maria", "_weapon_archangel",
    "_weapon_breakthrough", "_weapon_mox", "_weapon_pride",
    "_weapon_erebus", "_weapon_hawk", "_weapon_rasetsu",
]


# ── Save parsing ───────────────────────────────────────────────────────────────

def _save_timestamp(path: Path) -> datetime:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        ts = raw["Data"]["metadata"].get("timestampString", "")
        return datetime.strptime(ts, "%H:%M:%S, %d.%m.%Y")
    except Exception:
        return datetime.min


def find_save(save_name: str | None) -> Path:
    if save_name:
        sav = SAVE_ROOT / save_name / "sav.dat"
        if not sav.exists():
            sys.exit(f"[ERR] No sav.dat in {SAVE_ROOT / save_name}")
        return sav
    meta_candidates = list(SAVE_ROOT.glob("*/metadata.*.json"))
    if not meta_candidates:
        sys.exit(f"[ERR] No metadata.*.json found under {SAVE_ROOT}")
    latest_meta = max(meta_candidates, key=_save_timestamp)
    sav = latest_meta.parent / "sav.dat"
    if not sav.exists():
        sys.exit(f"[ERR] No sav.dat in {latest_meta.parent}")
    print(f"[i] Using save folder: {latest_meta.parent.name}")
    return sav


def build_hash_lookup() -> dict[int, str]:
    """Build CRC32 hash → TweakDB string lookup for Items.* entries."""
    tweakdb_path = TOOLS_DIR / "TweakDBIDs.json"
    if not tweakdb_path.exists():
        sys.exit(f"[ERR] TweakDBIDs.json not found at {tweakdb_path}")
    with tweakdb_path.open(encoding="utf-8") as f:
        all_ids: list[str] = json.load(f)
    result: dict[int, str] = {}
    for s in all_ids:
        if s.startswith("Items."):
            h = binascii.crc32(s.encode()) & 0xFFFFFFFF
            result[h] = s
    print(f"[i] TweakDB hash lookup: {len(result)} Items.* entries")
    return result


def scan_inventory(sav_path: Path, hash_to_str: dict[int, str]) -> set[str]:
    """Use CyberpunkPythonHacks to load the save and scan the inventory node."""
    hack_dir = TOOLS_DIR / "CyberpunkPythonHacks"
    if not hack_dir.exists():
        sys.exit(f"[ERR] CyberpunkPythonHacks not found at {hack_dir}")

    sys.path.insert(0, str(hack_dir))
    try:
        import cp2077chunk
        # Patch for v2.31 (capacity=512 = 0x200)
        cp2077chunk.DataChunkTableChunk.VALID_CAPACITY = (0x100, 0x200, 0x400)
        from cp2077save import SaveFile
    except ImportError as e:
        sys.exit(f"[ERR] Failed to import CyberpunkPythonHacks: {e}")

    sf = SaveFile(str(sav_path.parent))
    print(f"[i] Loaded save: {len(sf.nodes_info)} nodes")

    # Find the inventory node
    inv_idx = None
    for i, n in enumerate(sf.nodes_info):
        try:
            name = n.name.decode("ascii")
        except Exception:
            continue
        if name == "inventory":
            inv_idx = i
            break

    if inv_idx is None:
        sys.exit("[ERR] Could not find 'inventory' node in save")

    inv_node = sf.nodes_info[inv_idx]
    print(f"[i] Inventory node [{inv_idx}]: offset={inv_node.offset}, size={inv_node.size}")

    # Find end of all itemData children
    end_offset = inv_node.offset + inv_node.size
    for i in range(inv_idx + 1, len(sf.nodes_info)):
        n = sf.nodes_info[i]
        try:
            name = n.name.decode("ascii")
        except Exception:
            break
        if name == "itemData":
            end_offset = n.offset + n.size
        else:
            break

    total_bytes = end_offset - inv_node.offset
    print(f"[i] Reading {total_bytes:,} bytes of inventory data")
    inv_data = bytes(sf.data[inv_node.offset : end_offset])

    # Scan every 4-byte window for known item hashes
    found: set[str] = set()
    for i in range(0, len(inv_data) - 3):
        val = struct.unpack_from("<I", inv_data, i)[0]
        if val in hash_to_str:
            found.add(hash_to_str[val])

    print(f"[i] Found {len(found)} unique Items.* TweakDB entries in inventory")
    return found


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    save_name = sys.argv[1] if len(sys.argv) > 1 else None
    sav_path  = find_save(save_name)
    print(f"[i] Reading: {sav_path}")

    hash_to_str = build_hash_lookup()
    item_ids    = scan_inventory(sav_path, hash_to_str)

    # Resolve to tracked weapons
    owned: set[str] = set()
    for tweak_id, weapon_id in TWEAKDB_TO_WEAPON.items():
        if tweak_id in item_ids:
            owned.add(weapon_id)

    # Report
    print()
    print("=" * 60)
    print("ICONIC WEAPONS IN INVENTORY")
    print("=" * 60)
    for wid in TRACKED_WEAPONS:
        status = "✓ HAVE" if wid in owned else "○ MISSING"
        name   = wid.replace("_weapon_", "").replace("_", " ").title()
        print(f"  {status:10s}  {name}")

    print()
    have_count = len(owned)
    total      = len(TRACKED_WEAPONS)
    print(f"  {have_count}/{total} tracked iconic weapons in inventory")

    # Write JSON for tracker
    out = HERE / "tracker_weapons.json"
    result = {wid: (wid in owned) for wid in TRACKED_WEAPONS}
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\n[+] Written: {out}")
    print("    tracker_local.py will use this automatically on next run.")


if __name__ == "__main__":
    main()

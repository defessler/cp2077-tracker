"""
cp2077_save.py — Cyberpunk 2077 save-file parsing for the tracker engine.

Implements the save adapter contract required by tracker_engine:
  load_latest_save(save_root, save_name=None) -> dict (raw metadata)
  parse_save(raw, save_root, catalog)         -> SaveData dict

Primary data source: sav.dat via CyberpunkPythonHacks (tools/).
Requires CyberpunkPythonHacks installed at tools/CyberpunkPythonHacks/.

FactsDB binary format (per FactsTable node):
  [cp_packedint]  count N
  [uint32 × N]    FNV1a32 hashes of fact names (sorted ascending)
  [uint32 × N]    fact values (parallel array)
"""
from __future__ import annotations

import json
import re
import struct
import sys
from datetime import datetime, timedelta
from pathlib import Path


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt_time(seconds: float) -> str:
  td = timedelta(seconds=int(seconds))
  h  = td.days * 24 + td.seconds // 3600
  m  = (td.seconds % 3600) // 60
  return f"{h}h {m:02d}m"


def _fnv1a32(s: str) -> int:
  """FNV-1a 32-bit hash used by CP2077 for FactsDB fact names."""
  h = 0x811C9DC5
  for c in s.encode():
    h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
  return h


def _read_cp_packedint(data: bytes, off: int) -> tuple[int, int]:
  """CP2077 custom packed int (NOT standard LEB128). Returns (value, new_off)."""
  a = data[off]; off += 1
  val = a & 0x3F
  sign = bool(a & 0x80)
  if a & 0x40:
    a = data[off]; off += 1
    val |= (a & 0x7F) << 6
    if a & 0x80:
      a = data[off]; off += 1
      val |= (a & 0x7F) << 13
      if a & 0x80:
        a = data[off]; off += 1
        val |= (a & 0x7F) << 20
        if a & 0x80:
          a = data[off]; off += 1
          val |= (a & 0xFF) << 27
  return (-val if sign else val), off


# ── FactsDB parsing ────────────────────────────────────────────────────────────

def _wanted_fact_hashes(catalog: list[dict]) -> dict[int, str]:
  """FNV1a32 hash → fact name for every fact we need from FactsDB."""
  names: set[str] = set()
  for cat in catalog:
    for q in cat["quests"]:
      qid = q["id"]
      cid = q.get("check_id", qid)
      if q.get("check_fact"):
        names.add(q["check_fact"])
      if not qid.startswith("_weapon_"):
        # FactsDB uses only suffixed names — bare IDs never appear as fact names
        for n in (f"{qid}_done", f"{cid}_done",
                  f"{qid}_finished", f"{cid}_finished",
                  f"{qid}_active", f"{cid}_active"):
          names.add(n)
  # Facts used for choice flags / display
  names.update([
    "sq030_judy_lover", "sq012_fact_warn_river", "q003_royce_dead",
    "q103_helped_panam", "q110_voodoo_queen_dead", "q003_meredith_won",
    "sq026_maiko_dead", "q112_takemura_dead",
  ])
  return {_fnv1a32(n): n for n in names}


def _parse_facts_db(sav_path: Path, catalog: list[dict]) -> dict[str, int] | None:
  """
  Parse FactsDB from sav.dat. Returns {fact_name: value} for all recognized
  facts, or None if CyberpunkPythonHacks is unavailable or parse fails.
  """
  hack_dir = sav_path.parent.parent.parent / "tools" / "CyberpunkPythonHacks"
  # Also look relative to this file
  local_hack = Path(__file__).parent / "tools" / "CyberpunkPythonHacks"
  if local_hack.exists():
    hack_dir = local_hack
  if not hack_dir.exists():
    return None
  if str(hack_dir) not in sys.path:
    sys.path.insert(0, str(hack_dir))
  try:
    import cp2077chunk
    cp2077chunk.DataChunkTableChunk.VALID_CAPACITY = (0x100, 0x200, 0x400)
    from cp2077save import SaveFile
  except ImportError:
    return None
  try:
    sf = SaveFile(str(sav_path.parent))
  except Exception:
    return None

  wanted = _wanted_fact_hashes(catalog)
  result: dict[str, int] = {}
  for node in sf.nodes_info:
    try:
      if node.name.decode("ascii") != "FactsTable":
        continue
    except Exception:
      continue
    data = bytes(sf.data[node.offset : node.offset + node.size])
    off  = 4  # skip 4-byte node-index prefix from CyberpunkPythonHacks
    try:
      count, off = _read_cp_packedint(data, off)
      if count <= 0 or off + count * 8 > len(data):
        continue
      hashes = struct.unpack_from(f"<{count}I", data, off)
      values = struct.unpack_from(f"<{count}I", data, off + count * 4)
      for h, v in zip(hashes, values):
        if h in wanted:
          result[wanted[h]] = v
    except Exception:
      continue
  return result or None


def _parse_quest_rewards(sav_path: Path) -> set[str]:
  """
  Parse QuestProgressedAggregator_v3 from sav.dat.
  Returns reward keys like 'q112_old_friend' for completed quest phases.
  Used for mid-chain tracking when the parent ID isn't in finishedQuests yet.
  """
  hack_dir = Path(__file__).parent / "tools" / "CyberpunkPythonHacks"
  if not hack_dir.exists():
    return set()
  if str(hack_dir) not in sys.path:
    sys.path.insert(0, str(hack_dir))
  try:
    import cp2077chunk
    cp2077chunk.DataChunkTableChunk.VALID_CAPACITY = (0x100, 0x200, 0x400)
    from cp2077save import SaveFile
  except ImportError:
    return set()
  try:
    sf = SaveFile(str(sav_path.parent))
  except Exception:
    return set()

  rewards: set[str] = set()
  for node in sf.nodes_info:
    try:
      if node.name.decode("ascii") != "QuestProgressedAggregator_v3":
        continue
    except Exception:
      continue
    data = bytes(sf.data[node.offset : node.offset + node.size])
    for m in re.finditer(rb'[a-zA-Z0-9_\- ]{5,}', data):
      s = m.group().decode()
      if s.endswith(" reward"):
        rewards.add(s[:-7])
  return rewards


# ── Completion timestamps ──────────────────────────────────────────────────────

_TS_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


def _save_timestamp(path: Path) -> datetime:
  """Return parsed save datetime. Returns datetime.min on failure."""
  try:
    raw = json.loads(path.read_text(encoding="utf-8"))
    ts  = raw["Data"]["metadata"].get("timestampString", "")
    return datetime.strptime(ts, "%H:%M:%S, %d.%m.%Y")
  except Exception:
    return datetime.min


def _build_completion_timestamps(save_root: Path, catalog: list[dict]) -> dict[str, str]:
  """
  Scan all save metadata files chronologically. Returns {id: "DD Mon · HH:MM"}
  for the earliest save where each quest ID or check_fact first appeared.
  """
  candidates = list(save_root.glob("*/metadata.*.json"))
  if not candidates:
    return {}
  check_facts: set[str] = set()
  for cat in catalog:
    for q in cat["quests"]:
      if q.get("check_fact"):
        check_facts.add(q["check_fact"])

  timestamped = [(t, p) for p in candidates if (t := _save_timestamp(p)) != datetime.min]
  timestamped.sort(key=lambda x: x[0])

  first_seen: dict[str, datetime] = {}
  for ts, p in timestamped:
    try:
      m = json.loads(p.read_text(encoding="utf-8"))["Data"]["metadata"]
      for qid in m.get("finishedQuests", "").split():
        if qid and qid not in first_seen:
          first_seen[qid] = ts
      for entry in m.get("facts", []):
        key, _, val = entry.partition("=")
        key = key.strip()
        if val.strip() == "1" and key in check_facts and key not in first_seen:
          first_seen[key] = ts
    except Exception:
      continue

  return {
    k: f"{v.day} {_TS_MONTHS[v.month-1]} · {v.hour:02d}:{v.minute:02d}"
    for k, v in first_seen.items()
  }


# ── Tracker weapons (manual inventory scan) ────────────────────────────────────

def _load_tracker_weapons(base_dir: Path) -> dict[str, bool]:
  """Load tracker_weapons.json written by read_inventory.py."""
  p = base_dir / "tracker_weapons.json"
  if p.exists():
    try:
      return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
      pass
  return {}


# ── Public API ─────────────────────────────────────────────────────────────────

def load_latest_save(save_root: Path, save_name: str | None = None) -> dict:
  """Find and load the most recent save metadata JSON."""
  pattern    = f"{save_name}/metadata.*.json" if save_name else "*/metadata.*.json"
  candidates = list(save_root.glob(pattern))
  if not candidates:
    sys.exit(f"[ERR] No metadata JSON found under {save_root}")
  latest = max(candidates, key=_save_timestamp)
  print(f"[i] Reading save: {latest}")
  raw = json.loads(latest.read_text(encoding="utf-8"))
  raw["_sav_path"] = str(latest.parent / "sav.dat")
  return raw


def parse_save(raw: dict, save_root: Path, catalog: list[dict]) -> dict:
  """
  Parse a raw metadata dict into a SaveData dict for the tracker engine.

  SaveData contract (keys the engine expects):
    name, level, street_cred, life_path, play_time, difficulty,
    build_patch, timestamp, is_modded, has_ep1, attributes, choices
    finished_quests: list[str]   — all completed quest IDs
    active_facts:    list[str]   — named FactsDB flags that are non-zero
    quest_rewards:   list[str]   — reward keys from QuestProgressedAggregator_v3
    completed_at:    dict[str,str] — quest_id -> "DD Mon · HH:MM"
    manual_results:  dict[str,bool] — _weapon_* IDs -> found/not-found
  """
  m        = raw["Data"]["metadata"]
  sav_path = Path(raw.get("_sav_path", ""))

  # Primary: FactsDB
  sav_facts    = _parse_facts_db(sav_path, catalog) if sav_path.exists() else None
  quest_rewards = _parse_quest_rewards(sav_path)    if sav_path.exists() else set()

  if not sav_facts:
    sys.exit("[ERR] FactsDB parse failed — is CyberpunkPythonHacks installed in tools/?")

  # Build finished set from _done/_finished facts
  finished:     set[str] = set()
  active_facts: set[str] = set()
  for name, val in sav_facts.items():
    if val:
      active_facts.add(name)
      if name.endswith("_done"):
        finished.add(name[:-5])
      elif name.endswith("_finished"):
        finished.add(name[:-9])

  # Supplement: gigs (sts_*), activities (ma_*), and minor quests with no
  # FactsDB _done/_finished fact only appear in metadata finishedQuests.
  meta_finished = set(m.get("finishedQuests", "").split())
  extra = meta_finished - finished
  finished.update(extra)
  print(f"[i] FactsDB: {len(sav_facts)} facts resolved; +{len(extra)} supplement from finishedQuests")

  return {
    "name":           m.get("name", "?"),
    "level":          int(m.get("level", 0)),
    "street_cred":    int(m.get("streetCred", 0)),
    "life_path":      m.get("lifePath", "?"),
    "play_time":      fmt_time(m.get("playthroughTime", m.get("playTime", 0))),
    "difficulty":     m.get("difficulty", "?"),
    "build_patch":    m.get("buildPatch", "?"),
    "timestamp":      m.get("timestampString", "?"),
    "is_modded":      m.get("isModded", False),
    "has_ep1":        "EP1" in m.get("additionalContentIds", []),
    "attributes": {
      "Body":   int(m.get("strength", 0)),
      "Intel":  int(m.get("intelligence", 0)),
      "Reflex": int(m.get("reflexes", 0)),
      "Tech":   int(m.get("technicalAbility", 0)),
      "Cool":   int(m.get("cool", 0)),
    },
    "finished_quests": sorted(finished),
    "active_facts":    sorted(active_facts),
    "quest_rewards":   sorted(quest_rewards),
    "completed_at":    _build_completion_timestamps(save_root, catalog),
    "manual_results":  _load_tracker_weapons(Path(__file__).parent),
    "choices": {
      # Act 1
      "Royce":         ("q003_royce_dead"        in active_facts, "Killed",  "Spared",   "The_Heist"),
      "Militech":      ("q003_meredith_won"      in active_facts, "Meredith","Gilchrist","The_Heist"),
      # Act 2
      "Panam":         ("q103_helped_panam"      in active_facts, "Helped",  "Betrayed", "Ghost_Town_(quest)"),
      "Voodoo Queen":  ("q110_voodoo_queen_dead" in active_facts, "Dead",    "Alive",    "Gimme_Danger"),
      "Maiko":         ("sq026_maiko_dead"       in active_facts, "Killed",  "Spared",   "Pisces_(quest)"),
      "Takemura":      ("q112_takemura_dead"     not in active_facts, "Saved","Died",    "Search_and_Destroy"),
      # Romance
      "Judy":          ("sq030_judy_lover"       in active_facts, "Romanced","Friends",  "Pyramid_Song"),
      "River":         ("sq012_fact_warn_river"  in active_facts, "Warned",  "Silent",   "Following_the_River"),
      # Pending
      "PL epilogue":   ("q307"                   in finished,     "Done",    "Pending",  "Who_Wants_to_Live_Forever"),
      "Ending":        ("q113"                   in finished,     "Chosen",  "Pending",  "Nocturne_Op55N1"),
    },
  }

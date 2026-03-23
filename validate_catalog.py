#!/usr/bin/env python3
"""
validate_catalog.py  ·  CP2077 Tracker Data Validator
======================================================
Cross-references QUEST_CATALOG against:
  1. CDPR's official quest ID database (cdpr_quest_ids.md)
  2. The actual save file's finishedQuests
  3. Name consistency checks

Run:  python -X utf8 validate_catalog.py
"""

from __future__ import annotations
import json, re, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent

# ── Load CDPR reference ────────────────────────────────────────────────────────
ref_file = HERE / "cdpr_quest_ids.md"
if not ref_file.exists():
    sys.exit("[ERR] cdpr_quest_ids.md not found — run the fetch agent first")

content = ref_file.read_text(encoding="utf-8")

# Parse lines like: [Type] some/path/quest_id = Quest Name
CDPR: dict[str, str] = {}  # id → name
for m in re.finditer(r'\[(\w+)\]\s+\S+/(\S+)\s*=\s*(.+)', content):
    qtype, qid, name = m.group(1), m.group(2), m.group(3).strip()
    CDPR[qid] = name

# Also build a prefix lookup: "q101" → [q101_01_firestorm, q101_resurrection, ...]
from collections import defaultdict
PREFIX: dict[str, list[str]] = defaultdict(list)
for qid in CDPR:
    PREFIX[qid.split('_')[0]].append(qid)

print(f"CDPR database: {len(CDPR)} quest IDs loaded from {ref_file.name}")

# ── Load tracker catalog ───────────────────────────────────────────────────────
sys.path.insert(0, str(HERE))
from tracker_local import QUEST_CATALOG

catalog_entries: list[tuple[str, str, str]] = []  # (cat_label, id, name)
for cat in QUEST_CATALOG:
    for q in cat["quests"]:
        if not q["id"].startswith("_weapon_"):
            catalog_entries.append((cat["label"], q["id"], q["name"]))

print(f"Tracker catalog: {len(catalog_entries)} non-weapon quest entries")

# ── Load actual save ───────────────────────────────────────────────────────────
SAVE_ROOT = Path(r"C:\Users\defes\Saved Games\CD Projekt Red\Cyberpunk 2077")

def _save_ts(p: Path) -> datetime:
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        ts = raw["Data"]["metadata"].get("timestampString", "")
        return datetime.strptime(ts, "%H:%M:%S, %d.%m.%Y")
    except Exception:
        return datetime.min

candidates = list(SAVE_ROOT.glob("*/metadata.*.json"))
if candidates:
    latest = max(candidates, key=_save_ts)
    raw = json.loads(latest.read_text(encoding="utf-8"))
    SAVE_FINISHED: set[str] = set(raw["Data"]["metadata"].get("finishedQuests","").split())
    print(f"Save file:      {len(SAVE_FINISHED)} completed quests ({latest.parent.name})")
else:
    SAVE_FINISHED = set()
    print("Save file:      [not found]")

print()
print("=" * 72)

# ── Check 1: IDs in save but NOT in catalog ───────────────────────────────────
catalog_ids = {q[1] for q in catalog_entries}
uncatalogued = sorted(q for q in SAVE_FINISHED if q not in catalog_ids)
if uncatalogued:
    print(f"\n[!] COMPLETED IN SAVE BUT NOT IN CATALOG ({len(uncatalogued)}):")
    for qid in uncatalogued:
        cdpr_name = CDPR.get(qid, "")
        suffix = f" — '{cdpr_name}'" if cdpr_name else " — (not in CDPR DB)"
        print(f"    {qid}{suffix}")
else:
    print("\n[✓] All completed save quests are in the catalog")

# ── Check 2: Catalog IDs validated against CDPR DB ────────────────────────────
print(f"\n[?] CATALOG IDs vs CDPR DATABASE:")
validated, not_in_cdpr, name_mismatch = [], [], []

for cat_label, qid, our_name in catalog_entries:
    if qid in CDPR:
        # Exact match
        cdpr_name = CDPR[qid]
        if cdpr_name.lower() not in our_name.lower() and our_name.lower() not in cdpr_name.lower():
            name_mismatch.append((cat_label, qid, our_name, cdpr_name))
        else:
            validated.append(qid)
    elif qid in SAVE_FINISHED:
        # Not in CDPR DB but known from save — likely an arc/chain completion ID
        validated.append(qid)
    else:
        # Not in CDPR DB and never seen in save — possibly wrong
        not_in_cdpr.append((cat_label, qid, our_name))

print(f"    ✓ Verified (in CDPR DB or save): {len(validated)}")
print(f"    ✓ Name matches OK: {len(validated) - len(name_mismatch)}")

if name_mismatch:
    print(f"\n    [~] NAME MISMATCHES ({len(name_mismatch)}) — our name vs CDPR name:")
    for cat, qid, our, cdpr in name_mismatch:
        print(f"        [{cat}] {qid}")
        print(f"          Ours: {our}")
        print(f"          CDPR: {cdpr}")

if not_in_cdpr:
    print(f"\n    [?] NOT IN CDPR DB AND NOT SEEN IN SAVE ({len(not_in_cdpr)}):")
    print(f"        (These may be story arc completions or incorrect IDs)")
    for cat, qid, name in not_in_cdpr:
        print(f"        [{cat}] {qid} — '{name}'")

# ── Check 3: CDPR DB gig/NCPD IDs not in catalog ────────────────────────────
print(f"\n[?] CDPR DB ENTRIES MISSING FROM CATALOG:")
cdpr_gigs    = {k for k in CDPR if k.startswith("sts_")}
cdpr_ncpd    = {k for k in CDPR if k.startswith("ma_")}
cdpr_sq      = {k for k in CDPR if k.startswith("sq")}
cdpr_mq      = {k for k in CDPR if k.startswith("mq")}

for label, cdpr_set in [("Gigs (sts_*)", cdpr_gigs), ("NCPD/Cyberpsycho (ma_*)", cdpr_ncpd),
                         ("Side Jobs (sq*)", cdpr_sq), ("Minor Quests (mq*)", cdpr_mq)]:
    missing = sorted(cdpr_set - catalog_ids)
    if missing:
        print(f"\n    {label} — {len(missing)} in CDPR DB but not tracked:")
        for qid in missing:
            print(f"        {qid} — {CDPR[qid]}")
    else:
        print(f"    ✓ {label}: all CDPR IDs present in catalog")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 72)
total = len(catalog_entries)
issues = len(not_in_cdpr) + len(name_mismatch)
pct = round(100 * (total - issues) / total)
print(f"\nSUMMARY: {total - issues}/{total} catalog entries validated ({pct}%)")
if issues == 0:
    print("All catalog entries verified against CDPR database and/or save file.")
else:
    print(f"  {len(name_mismatch)} name mismatches, {len(not_in_cdpr)} unverified IDs")
    print("  Review the items flagged above.")

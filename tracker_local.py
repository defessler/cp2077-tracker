#!/usr/bin/env python3
"""
tracker_local.py  ·  Cyberpunk 2077 100% Completion Tracker
=============================================================
Reads your most recent save and generates a local HTML dashboard.

USAGE
──────
    python tracker_local.py                  # newest save, open browser
    python tracker_local.py --save QuickSave-3
    python tracker_local.py --no-open        # generate file, don't open
"""
from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from cp2077_catalog import QUEST_CATALOG, LIFE_PATH_TAG, SUPPRESS_IDS
from cp2077_save    import load_latest_save, parse_save
from tracker_engine import build_catalog_data, generate_html

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SAVE_ROOT   = Path.home() / "Saved Games" / "CD Projekt Red" / "Cyberpunk 2077"
OUTPUT_FILE = Path(__file__).parent / "tracker_dashboard.html"
GAME_TITLE  = "CP2077 · 100% Tracker"
WIKI_BASE   = "https://cyberpunk.fandom.com/wiki/"


def main() -> None:
  parser = argparse.ArgumentParser(description="CP2077 100% Completion Tracker")
  parser.add_argument("--save",    metavar="FOLDER")
  parser.add_argument("--no-open", action="store_true")
  parser.add_argument("--output",  metavar="FILE", default=str(OUTPUT_FILE))
  args = parser.parse_args()

  raw  = load_latest_save(SAVE_ROOT, args.save)
  save = parse_save(raw, SAVE_ROOT, QUEST_CATALOG)

  catalog = build_catalog_data(save, QUEST_CATALOG,
                                life_path_tags=LIFE_PATH_TAG,
                                suppress_ids=SUPPRESS_IDS)

  total = sum(c["total"]     for c in catalog if c["id"] != "uncatalogued")
  done  = sum(c["completed"] for c in catalog if c["id"] != "uncatalogued")
  print(f"[+] {save['name']}  Level {save['level']}  {save['play_time']}")
  print(f"[+] Overall: {done}/{total}  ({round(100*done/total)}%)")
  for c in catalog:
    bar = "#" * (c["pct"] // 5) + "." * (20 - c["pct"] // 5)
    print(f"    {bar}  {c['pct']:3d}%  {c['completed']:3d}/{c['total']:<3d}  {c['label']}")

  out = Path(args.output)
  generate_html(save, catalog, out, game_title=GAME_TITLE, wiki_base_url=WIKI_BASE)
  print(f"[+] Written: {out}")

  if not args.no_open:
    webbrowser.open(out.as_uri())


if __name__ == "__main__":
  main()

# Cyberpunk 2077 — 100% Completion Tracker

A local HTML dashboard that reads your Cyberpunk 2077 save file and tracks completion across every content category: main story, side jobs, gigs, cyberpsycho sightings, NCPD crimes, iconic weapons, and Phantom Liberty.

**Live preview:** https://defessler.github.io/game-tools/cp2077-tracker.html

---

## Features

- Reads your latest save automatically (by in-save timestamp, not file date)
- Tracks 340+ activities across 15 categories
- Wiki-validated quest catalog — names and IDs cross-referenced against the CDPR modding reference
- Per-quest wiki links to cyberpunk.fandom.com
- Sidebar progress bars per category with clickable navigation
- URL hash navigation (`#side_jobs`, `#phantom_liberty`, etc.) with browser back/forward support
- Filter by completion status, search by name or tag
- In-page **⚑ Report** button (hover any quest) to queue formatted bug reports
- Iconic weapon inventory scanner (reads `sav.dat` via CyberpunkPythonHacks)
- Completed categories marked with ☑ checkbox in the category grid

---

## Files

| File | Purpose |
|------|---------|
| `tracker_local.py` | Entry point — configure paths here, run to generate dashboard |
| `cp2077_catalog.py` | Quest catalog, suppress IDs, life-path tag map |
| `cp2077_save.py` | CP2077 save adapter — reads metadata.json + sav.dat FactsDB |
| `tracker_engine.py` | Generic engine — completion logic, HTML template |
| `tracker_dashboard.html` | Generated output — open in browser |
| `read_inventory.py` | Scans `sav.dat` for iconic weapons → `tracker_weapons.json` |
| `validate_catalog.py` | Cross-references catalog against CDPR quest ID database |

---

## Setup

### Requirements

- Python 3.10+
- No pip dependencies for the main tracker (pure stdlib)

### Save path

Edit `SAVE_ROOT` at the top of `tracker_local.py`:

```python
SAVE_ROOT = Path(r"C:\Users\YourName\Saved Games\CD Projekt Red\Cyberpunk 2077")
```

### Usage

```bash
# Generate dashboard and open in browser
python tracker_local.py

# Generate without opening
python tracker_local.py --no-open

# Use a specific save folder
python tracker_local.py --save AutoSave-5

# Scan inventory for iconic weapons (optional)
python read_inventory.py
```

---

## Iconic Weapon Scanner (optional)

`read_inventory.py` reads the binary `sav.dat` to detect which iconic weapons are in your inventory. It requires:

1. **[CyberpunkPythonHacks](https://github.com/farzher/CyberpunkPythonHacks)** — place in `tools/CyberpunkPythonHacks/`
2. **TweakDBIDs.json** — place in `tools/TweakDBIDs.json` (available from the [Cyberpunk modding community](https://wiki.redmodding.org/))

A compatibility patch is applied automatically for save version 2.31:

```python
cp2077chunk.DataChunkTableChunk.VALID_CAPACITY = (0x100, 0x200, 0x400)
```

Once run, `tracker_weapons.json` is written and picked up automatically by `tracker_local.py` on the next run. You can also click any iconic weapon row in the dashboard to toggle it manually — state is stored in browser localStorage.

---

## Save Format Notes

- Save root: `%USERPROFILE%\Saved Games\CD Projekt Red\Cyberpunk 2077`
- Latest save is detected by parsing `timestampString` from inside the metadata JSON — more reliable than file modification time since CP2077 cycles autosave slots
- `finishedQuests` is a space-separated string of completed quest IDs
- Only **parent IDs** appear (e.g. `q105`, not `q105_dollhouse`); phase-split quests use `check_id` to map display entries to the parent
- FactsDB in `sav.dat` provides richer completion data (`_done`/`_finished` facts) and is required — CyberpunkPythonHacks must be installed

---

## Reconciling Save Data

When the dashboard shows an "Uncatalogued" category, those are quest IDs present in your save that the tracker doesn't recognize. To investigate:

1. Run `tracker_local.py` — uncatalogued IDs are printed and shown in the dashboard
2. Look up the ID in the [CDPR modding wiki](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/reference-quest-ids)
3. Decide the correct action:

| Situation | Fix |
|-----------|-----|
| It's a real quest, not in catalog | Add it to `QUEST_CATALOG` in `cp2077_catalog.py` |
| It's a parent ID that's already tracked via sub-quests | Add to `SUPPRESS_IDS` in `cp2077_catalog.py` |
| It's a secondary/duplicate ID for a tracked quest | Add to `SUPPRESS_IDS` |
| It's a sandbox/airdrop/internal event with no journal entry | Add to `SUPPRESS_IDS` |

Use the **⚑ Report** button in the dashboard to queue issues and copy them all at once.

---

## Adding Another Game

The engine (`tracker_engine.py`) is game-agnostic. To track a new game:

### 1. Create `mygame_catalog.py`

```python
QUEST_CATALOG = [
  {
    "id": "main_story", "label": "Main Story", "color": "#00d4ff", "icon": "◈",
    "tags": ["main-story"],
    "quests": [
      {"id": "quest_001", "name": "Opening Act", "tags": ["act1"]},
      # check_id: override which ID to look up in finished_quests
      # check_fact: use a named flag instead of finished_quests
      # reward_key: use a reward aggregator key
      # wiki: None=auto-generate, False=suppress, "Slug"=use this slug
    ],
  },
  # Manual collectibles — prefix IDs with '_' to enable click-to-toggle
  {
    "id": "collectibles", "label": "Collectibles", "color": "#f0e040", "icon": "⚔",
    "note": "Click any row to mark as collected",
    "quests": [
      {"id": "_item_sword", "name": "The Legendary Sword", "tags": ["weapon"]},
    ],
  },
]

LIFE_PATH_TAG = None   # or {"ClassName": "class-tag"} if game has life paths

SUPPRESS_IDS: set[str] = {
  # IDs that appear in finished_quests but aren't real trackable quests
  "parent_flag_001",
}
```

### 2. Create `mygame_save.py`

Implement two functions:

```python
def load_latest_save(save_root: Path, save_name: str | None = None) -> dict:
    """Find and load the most recent save file. Return raw save data."""
    ...

def parse_save(raw: dict, save_root: Path, catalog: list[dict]) -> dict:
    """Parse raw save into SaveData dict.

    Required keys:
      finished_quests: list[str]    — completed activity IDs
      active_facts:    list[str]    — active named flags
      quest_rewards:   list[str]    — reward aggregator keys
      completed_at:    dict[str,str] — id -> "DD Mon · HH:MM"
      manual_results:  dict[str,bool] — _prefixed IDs -> True/False
      choices:         dict[str,bool] — display flags for sidebar

    Plus display fields: name, level, play_time, etc.
    """
    ...
```

### 3. Create `mygame_local.py`

```python
from pathlib import Path
import argparse, webbrowser
from mygame_catalog import QUEST_CATALOG, LIFE_PATH_TAG, SUPPRESS_IDS
from mygame_save    import load_latest_save, parse_save
from tracker_engine import build_catalog_data, generate_html

SAVE_ROOT   = Path(r"C:\path\to\saves")
OUTPUT_FILE = Path(__file__).parent / "mygame_dashboard.html"
GAME_TITLE  = "My Game · Tracker"
WIKI_BASE   = "https://mygame.wiki.gg/wiki/"  # or "" to disable wiki links

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    raw     = load_latest_save(SAVE_ROOT)
    save    = parse_save(raw, SAVE_ROOT, QUEST_CATALOG)
    catalog = build_catalog_data(save, QUEST_CATALOG,
                                  life_path_tags=LIFE_PATH_TAG,
                                  suppress_ids=SUPPRESS_IDS)
    generate_html(save, catalog, OUTPUT_FILE,
                  game_title=GAME_TITLE, wiki_base_url=WIKI_BASE)
    if not args.no_open:
        webbrowser.open(OUTPUT_FILE.as_uri())

if __name__ == "__main__":
    main()
```

---

## Quest Catalog

The catalog in `cp2077_catalog.py` covers:

| Category | Count |
|----------|-------|
| Main Story (Acts 1–3 + epilogues) | 39 |
| Side Jobs | 35 |
| Phantom Liberty (main + both path branches) | 26 |
| PL Side Quests & Activities | 17 |
| Minor Activities | 49 |
| Gigs (all 6 districts + Dogtown) | 87 |
| Cyberpsycho Sightings | 17 |
| NCPD Reported Crimes | 45 |
| Iconic Weapons | 34 |

Quest IDs are validated against the [CDPR modding wiki](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/reference-quest-ids).

### Phase-split quests

Some quests share a parent ID in `finishedQuests` but appear as separate journal entries. These use a `check_id` field pointing to the parent while displaying the individual phase name:

```python
{"id": "q105_dollhouse", "name": "Automatic Love", "check_id": "q105", ...}
{"id": "q105_02_jigjig",  "name": "The Space in Between", "check_id": "q105", ...}
```

---

## Reporting Issues

Use the **⚑ Report** button (hover any quest row in the dashboard) to queue a formatted bug report. Common issues:

- Quest shows wrong completion status
- Wrong or missing wiki link
- Quest should be split into separate entries (or merged)
- Missing quest not in catalog

---

## Credits

- Save parsing: [CyberpunkPythonHacks](https://github.com/farzher/CyberpunkPythonHacks) by Ali Farzanrad
- Quest IDs: [CDPR Modding Wiki](https://wiki.redmodding.org/cyberpunk-2077-modding/)
- Wiki links: [Cyberpunk 2077 Wiki (Fandom)](https://cyberpunk.fandom.com/)

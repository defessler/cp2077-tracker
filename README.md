# Cyberpunk 2077 — 100% Completion Tracker

A local HTML dashboard that reads your Cyberpunk 2077 save file and tracks completion across every content category: main story, side jobs, gigs, cyberpsycho sightings, NCPD crimes, iconic weapons, and Phantom Liberty.

![screenshot placeholder](https://defessler.github.io/game-tools/cp2077-tracker.html)

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
- In-page **⚑ Report** button (hover any quest) to copy a formatted bug report
- Iconic weapon inventory scanner (reads `sav.dat` via CyberpunkPythonHacks)
- Google Sheets sync script for weapon tracking

---

## Files

| File | Purpose |
|------|---------|
| `tracker_local.py` | Main script — reads save, generates `tracker_dashboard.html` |
| `read_inventory.py` | Scans `sav.dat` for iconic weapons → `tracker_weapons.json` |
| `validate_catalog.py` | Cross-references catalog against CDPR quest ID database |
| `cyberpunk_tracker.py` | Google Sheets sync (optional, requires Google API setup) |
| `cdpr_quest_ids.md` | CDPR modding wiki quest ID reference |

---

## Setup

### Requirements

- Python 3.10+
- No pip dependencies for the main tracker (pure stdlib)

### Save path

Edit `SAVE_ROOT` at the top of `tracker_local.py` and `read_inventory.py` to match your save directory:

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

# Validate catalog against CDPR quest IDs
python validate_catalog.py
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

Once run, `tracker_weapons.json` is written and picked up automatically by `tracker_local.py` on the next run.

---

## Google Sheets Sync (optional)

`cyberpunk_tracker.py` syncs quest completion and weapon status to a Google Sheet. Requires:

1. `pip install gspread google-auth-oauthlib`
2. A Google Cloud project with Sheets API enabled
3. OAuth 2.0 credentials saved as `oauth_client.json` in the project folder

See the setup instructions at the top of `cyberpunk_tracker.py`.

---

## Quest Catalog

The catalog in `tracker_local.py` covers:

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

Use the **⚑ Report** button (hover any quest row in the dashboard) to copy a formatted bug report. Common issues:

- Quest shows wrong completion status
- Wrong or missing wiki link
- Quest should be split into separate entries (or merged)
- Missing quest not in catalog

---

## Save Format Notes

- Save root: `%USERPROFILE%\Saved Games\CD Projekt Red\Cyberpunk 2077`
- Latest save is detected by parsing `timestampString` from inside the metadata JSON — more reliable than file modification time since CP2077 cycles autosave slots
- `finishedQuests` is a space-separated string of completed quest IDs
- Only **parent IDs** appear (e.g. `q105`, not `q105_dollhouse`)
- Play time uses `playthroughTime` (matches the in-game load screen display)

---

## Credits

- Save parsing: [CyberpunkPythonHacks](https://github.com/farzher/CyberpunkPythonHacks) by Ali Farzanrad
- Quest IDs: [CDPR Modding Wiki](https://wiki.redmodding.org/cyberpunk-2077-modding/)
- Wiki links: [Cyberpunk 2077 Wiki (Fandom)](https://cyberpunk.fandom.com/)

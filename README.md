# Cyberpunk 2077 — 100% Completion Tracker

Reads your CP2077 save and generates a local HTML dashboard tracking completion across 334 activities: main story, side jobs, gigs, cyberpsychos, NCPD crimes, iconic weapons, and Phantom Liberty.

---

## Usage

```bash
python tracker_local.py              # generate dashboard, open in browser
python tracker_local.py --no-open   # generate without opening
python tracker_local.py --save AutoSave-5  # specific save slot
python read_inventory.py            # scan sav.dat for iconic weapons
```

Saves are read from `%USERPROFILE%\Saved Games\CD Projekt Red\Cyberpunk 2077` automatically. Override `SAVE_ROOT` at the top of `tracker_local.py` if needed.

### Requirements
- Python 3.10+ (stdlib only — no pip dependencies for the main tracker)
- [CyberpunkPythonHacks](https://github.com/farzher/CyberpunkPythonHacks) in `tools/CyberpunkPythonHacks/` (required for FactsDB and weapon scanning)
- `TweakDBIDs.json` in `tools/` (for weapon scanner only — from the [CDPR modding community](https://wiki.redmodding.org/))

---

## Files

| File | Purpose |
|------|---------|
| `tracker_local.py` | Entry point |
| `cp2077_catalog.py` | Quest catalog, path tags, suppress IDs |
| `cp2077_save.py` | Save adapter — reads metadata.json + sav.dat |
| `tracker_engine.py` | Game-agnostic engine + HTML template |
| `tracker_dashboard.html` | Generated output |
| `tracker_weapons.json` | Manual overrides — iconic weapons + undetectable quests |
| `read_inventory.py` | Writes tracker_weapons.json from sav.dat inventory scan |

---

## Adding Another Game

The engine (`tracker_engine.py`) is game-agnostic. To track a new game:

1. **`mygame_catalog.py`** — define `QUEST_CATALOG`, `LIFE_PATH_TAG`, `SUPPRESS_IDS`
2. **`mygame_save.py`** — implement `load_latest_save()` and `parse_save()` returning a SaveData dict with: `finished_quests`, `active_facts`, `quest_rewards`, `completed_at`, `manual_results`, `choices`, plus display fields (`name`, `level`, `play_time`, etc.)
3. **`mygame_local.py`** — thin entry point, ~40 lines (see `tracker_local.py`)

The SaveData contract is documented in the docstring at the top of `tracker_engine.py`.

---

## Credits

- Save parsing: [CyberpunkPythonHacks](https://github.com/farzher/CyberpunkPythonHacks) by Ali Farzanrad
- Quest IDs: [CDPR Modding Wiki](https://wiki.redmodding.org/cyberpunk-2077-modding/)
- Wiki links: [Cyberpunk 2077 Wiki (Fandom)](https://cyberpunk.fandom.com/)

---

<details>
<summary>⚠️ Spoilers — CP2077 save format, quest mechanics, and discovery notes</summary>

## How CP2077 Saves Work

Each save slot contains two files:

- **`metadata.*.json`** — a JSON summary written by the game: player level, life path, playtime, and critically, `finishedQuests` — a space-separated string of completed quest IDs. This is the only place quest completion is recorded in a human-readable form.
- **`sav.dat`** — the full binary save. A custom chunked format parsed by CyberpunkPythonHacks. Contains game state nodes keyed by name.

### finishedQuests

The `finishedQuests` string only contains **parent IDs** — the internal group ID for a quest chain, not the individual phase IDs. For example, the entire Automatic Love chain (four separate journal entries) all appear as `q105` in finishedQuests.

This means quests that appear as separate items in the in-game journal must be mapped to their parent ID in the catalog using `check_id`. Individual phase IDs like `q105_dollhouse` never appear in finishedQuests.

Some IDs in finishedQuests aren't real quests at all — they're parent group flags (e.g. `q000`, `q001`), duplicate IDs the game writes twice (e.g. `we_ep1_01` and `mq301` for the same quest), or internal sandbox/airdrop event IDs. These are all in `SUPPRESS_IDS` in `cp2077_catalog.py`.

### FactsDB (sav.dat → FactsTable node)

The save's `FactsTable` node contains ~29,085 entries. Each entry is a pair of 32-bit unsigned integers: an FNV1a32 hash of the fact name, and its value. **No name strings are stored** — the game hashes fact names at runtime and never writes them to disk.

To read a specific fact, you compute `FNV1a32("fact_name")` and scan for it. The tracker pre-computes hashes for all known fact names derived from the quest catalog (e.g. `{qid}_done`, `{qid}_finished`) plus a set of manually-discovered outcome flags. Of 29,085 facts in a typical save, roughly 209 are resolved.

Facts cover things `finishedQuests` can't: mid-chain completion states, NPC outcomes, romance flags, and world-state choices.

### QuestProgressedAggregator_v3 (sav.dat)

This node contains plain ASCII strings — reward keys written when a quest phase completes and grants a reward. It's used for a small number of quests where neither a `_done` fact nor a finishedQuests entry exists but a reward phase string does. Example: `mq036_money_back reward` signals that the Sweet Dreams phone-call phase has triggered.

---

## What We Had to Figure Out

Building the catalog required cross-referencing multiple sources and probing the save directly.

**Quest IDs** came from the [CDPR modding wiki quest ID reference](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/reference-quest-ids). Every quest, gig, and activity has an internal ID that may differ from its display name.

**Audit loop** — the tracker reports any ID in `finishedQuests` that isn't in the catalog as "Uncatalogued". Running the tracker against a real save, looking up each unknown ID, and deciding whether to add it to the catalog or suppress it was done iteratively. This surfaced:
- Parent group flags written alongside their children (suppressed)
- Duplicate IDs CP2077 writes for the same quest (`we_ep1_01` and `mq301` both appear for "Balls to the Wall")
- Sandbox/airdrop IDs with no journal entry (suppressed)

**Phase splits** — some quests share a parent ID in finishedQuests but appear as separate journal entries. These had to be identified by comparing what the wiki lists as separate quests vs what the save actually records.

**FactsDB discovery** — fact names are not stored anywhere accessible. To find them, we guessed naming patterns (`{qid}_done`, `{npc}_dead`, `{sq}_lover`) and computed FNV1a32 hashes, then scanned the FactsTable for matches. This is how choice flags like `q003_royce_dead`, `q306_reed_killed`, and `sq030_judy_lover` were found. Many attempted names returned no match — the game's internal naming is inconsistent and undocumented.

**PL path detection** — the Reed vs Songbird choice (Firestarter, q304) doesn't write a fact with an obvious name. After exhaustive probing, `q306_reed_killed = 1` was found in the FactsDB for Songbird-path saves. This is used to derive `pl_path` and filter Reed-exclusive quests out of the count (they appear as dimmed "branch" rows via the Branches toggle).

**q305_done doesn't exist** — the Phantom Liberty q305 quest chain completes without writing a `q305_done` fact. Since q306 cannot be reached without completing q305, q305 completion is inferred from `q306_done`.

**mq045 (Paid in Full)** — confirmed undetectable. The quest (pay Viktor back his eddies) completes with no FactsDB fact, no finishedQuests entry, and no aggregator string. Stored as a manual confirmation in `tracker_weapons.json`.

**Gigs and NCPD crimes** — these never write FactsDB facts. They only appear in `finishedQuests`. This is by design; the tracker always supplements FactsDB results with finishedQuests for this reason.

---

## Progress Tracking — Priority Order

| Priority | Source | Used for |
|----------|--------|----------|
| 1 | `tracker_weapons.json` | Manual overrides — weapons + undetectable quests |
| 2 | FactsDB (`sav.dat` FactsTable) | Quest `_done` facts, NPC outcomes, choices, path detection |
| 3 | QuestProgressedAggregator_v3 | Mid-chain reward phase strings |
| 4 | `finishedQuests` (metadata.json) | Gigs, NCPD crimes, most quests |
| 5 | Derived | Life path → prologue filter; `q306_reed_killed` → PL path filter |

### Known undetectable quests

| Quest | Reason | Fix |
|-------|--------|-----|
| mq045 Paid in Full | Single-interaction payment; no fact, no finishedQuests entry | Set `"mq045": true` in `tracker_weapons.json` |

---

## Reconciling the Catalog

When the dashboard shows an **Uncatalogued** category, those IDs are in your save but not in the catalog. To resolve:

1. Look up the ID in the [CDPR quest ID reference](https://wiki.redmodding.org/cyberpunk-2077-modding/for-mod-creators-theory/references-lists-and-overviews/reference-quest-ids)
2. Decide:

| Situation | Action |
|-----------|--------|
| Real quest missing from catalog | Add to `QUEST_CATALOG` in `cp2077_catalog.py` |
| Parent ID already tracked via children | Add to `SUPPRESS_IDS` |
| Duplicate ID for a tracked quest | Add to `SUPPRESS_IDS` |
| Internal/sandbox ID with no journal entry | Add to `SUPPRESS_IDS` |

Use the **⚑ Report** button on any quest row to queue a formatted bug report.

</details>

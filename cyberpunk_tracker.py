#!/usr/bin/env python3
"""
cyberpunk_tracker.py  ·  Cyberpunk 2077 Save → Google Sheets Iconic Weapon Tracker
====================================================================================

Reads your most recent Cyberpunk 2077 save, checks which missions are complete,
then updates the "Full List" sheet with a QUEST STATUS column and adds/refreshes
a "📊 My Progress" tab with player stats.

SETUP (one-time)
─────────────────
1.  Install dependencies:
        pip install gspread google-auth-oauthlib

2.  Go to https://console.cloud.google.com/
      • Create a project (e.g. "CP2077 Tracker")
      • APIs & Services → Library → enable "Google Sheets API"
      • APIs & Services → OAuth consent screen
            – User type: External
            – Add your Gmail as a Test User
      • APIs & Services → Credentials → Create Credentials
            → OAuth 2.0 Client ID → Desktop app → Download JSON
      • Rename the downloaded file to  oauth_client.json
        and put it in the same folder as this script.

3.  Run once — a browser tab opens for Google sign-in:
        python cyberpunk_tracker.py

    After that, token.json caches your auth so future runs are silent.

USAGE
──────
    python cyberpunk_tracker.py                  # auto-finds newest save
    python cyberpunk_tracker.py --save AutoSave-11   # specific save folder
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
SAVE_ROOT  = Path(r"C:\Users\defes\Saved Games\CD Projekt Red\Cyberpunk 2077")
SHEET_ID   = "1ugtq8_n0zBS0gBuqrKVknJ1IM892fuoXabVBjFT6oHI"
OAUTH_FILE = Path(__file__).parent / "oauth_client.json"
TOKEN_FILE = Path(__file__).parent / "token.json"
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets"]

STATUS_COL_HEADER = "QUEST STATUS"  # column that will be written into Full List

# ── MISSION NAME → INTERNAL QUEST IDs ─────────────────────────────────────────
# Keys are substrings that appear in the spreadsheet MISSION column.
# Values are internal quest IDs from the save's finishedQuests field.
# An empty list means the weapon needs no quest (open world / vendor).
MISSION_TO_IDS: dict[str, list[str]] = {
    # Prologue / Act 1
    "The Rescue":                       ["mq001"],
    "The Ripperdoc":                    ["mq002"],
    "The Corpo-Rat":                    ["mq003"],
    "The Street Kid":                   ["mq008"],
    "The Nomad":                        ["mq005"],
    "Practice Makes Perfect":           ["mq010"],
    "The Pickup":                       ["q003"],
    "The Information":                  ["q004"],
    "The Heist":                        ["mq301"],
    # Act 2 main quests
    "Playing for Time":                 ["mq011"],
    "Automatic Love":                   ["mq012"],
    "The Space In Between":             ["mq013"],
    "Disasterpiece":                    ["mq014"],
    "Ex-Factor":                        ["mq015"],
    "Talkin' Bout a Revolution":        ["mq016"],
    "Ghost Town":                       ["mq021"],
    "Life During Wartime":              ["mq023"],
    "Lightning Breaks":                 ["mq022"],
    "We Gotta Live Together":           ["mq032"],
    "With a Little Help From My Friends": ["mq033"],
    "With a Little Help":               ["mq033"],
    "Both Sides, Now":                  ["mq035"],
    "Riders on the Storm":              ["mq038"],
    "I'll Fly Away":                    ["mq025"],
    "Queen of the Highway":             ["mq041"],
    # Side jobs
    "The Gun":                          ["sq_q001_wakako"],
    "Shoot to Thrill":                  [],            # Wilson's range, no quest gate
    "Losing My Religion":               ["sq006"],
    "Big in Japan":                     ["sq006"],
    "Beat on the Brat":                 ["sq004"],
    "Heroes":                           ["mq301"],
    "Stadium Love":                     ["mq011"],
    "Venus in Furs":                    ["mq012"],
    "The Hunt":                         ["sq012"],
    "Following the River":              ["sq012"],
    "I Fought The Law":                 ["sq018"],
    "Pisces":                           ["sq030"],
    "Pyramid Song":                     ["sq024"],
    "Machine Gun":                      ["mq011"],
    # Phantom Liberty
    "Somewhat Damaged":                 ["sa_ep1_32"],
    "The Damned":                       ["sa_ep1_32"],
    "Dog Eat Dog":                      ["sa_ep1_32"],
    "Treating Symptoms":                ["sa_ep1_32"],
    "Spy in the Jungle":                ["sa_ep1_32"],
    "Black Steel in the Hour of Chaos": ["sa_ep1_32"],
    "Firestarter":                      ["sa_ep1_32"],
    "Birds With Broken Wings":          ["sa_ep1_32"],
    "You Know My Name":                 ["sa_ep1_32"],
    "Roads to Redemption":              ["sa_ep1_32"],
    "From Her to Eternity":             ["sa_ep1_32"],
}

# Extra save "facts" that must be active (=1) for specific weapons,
# checked in addition to the quest IDs above.
WEAPON_EXTRA_FACTS: dict[str, list[str]] = {
    "Chaos":        ["q003_royce_dead"],      # must have killed Royce
    "Widow Maker":  ["q103_helped_panam"],    # must have chosen to fight Nash with Panam
    "Mox":          ["sq030_judy_lover"],     # must have romanced Judy
}

# Weapon name substrings that are always open-world (no quest or condition).
OPEN_WORLD_WEAPONS = {
    "Dying Night", "Guts", "Blue Fang", "Headhunter",
}


# ── HELPERS ───────────────────────────────────────────────────────────────────

def col_letter(n: int) -> str:
    """Convert 1-indexed column number to A1-notation letter(s)."""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def fmt_time(seconds: float) -> str:
    td = timedelta(seconds=int(seconds))
    total_h = td.days * 24 + td.seconds // 3600
    mins = (td.seconds % 3600) // 60
    return f"{total_h}h {mins:02d}m"


def _save_timestamp(path: Path) -> datetime:
    """Return parsed save datetime for sorting. Returns datetime.min on failure."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        ts = raw["Data"]["metadata"].get("timestampString", "")
        return datetime.strptime(ts, "%H:%M:%S, %d.%m.%Y")
    except Exception:
        return datetime.min


def load_latest_save(save_name: str | None) -> dict:
    """Find and parse the most recent metadata JSON from the save directory."""
    pattern = f"{save_name}/metadata.*.json" if save_name else "*/metadata.*.json"
    candidates = list(SAVE_ROOT.glob(pattern))
    if not candidates:
        sys.exit(f"[ERR] No metadata JSON found under {SAVE_ROOT}")
    latest = max(candidates, key=_save_timestamp)
    print(f"[i] Reading save: {latest}")
    return json.loads(latest.read_text(encoding="utf-8"))


def parse_save(raw: dict) -> dict:
    """Extract the fields we care about from the raw metadata JSON."""
    m = raw["Data"]["metadata"]

    finished: set[str] = set(m.get("finishedQuests", "").split())

    # facts look like "sq030_judy_lover=1"; build a set of those equal to 1
    active_facts: set[str] = set()
    for entry in m.get("facts", []):
        key, _, val = entry.partition("=")
        if val.strip() == "1":
            active_facts.add(key.strip())

    return {
        "name":          m.get("name", "?"),
        "level":         int(m.get("level", 0)),
        "street_cred":   int(m.get("streetCred", 0)),
        "life_path":     m.get("lifePath", "?"),
        "body_gender":   m.get("bodyGender", "?"),
        "play_time":     fmt_time(m.get("playTime", 0)),
        "difficulty":    m.get("difficulty", "?"),
        "build_patch":   m.get("buildPatch", "?"),
        "timestamp":     m.get("timestampString", "?"),
        "is_modded":     m.get("isModded", False),
        "has_ep1":       "EP1" in m.get("additionalContentIds", []),
        "attributes": {
            "Body":              int(m.get("strength", 0)),
            "Intelligence":      int(m.get("intelligence", 0)),
            "Reflexes":          int(m.get("reflexes", 0)),
            "Technical Ability": int(m.get("technicalAbility", 0)),
            "Cool":              int(m.get("cool", 0)),
        },
        "finished_quests": finished,
        "active_facts":    active_facts,
    }


def weapon_status(name: str, mission: str, req: str,
                  finished: set[str], facts: set[str]) -> str:
    """Return a status string for a single weapon row."""
    base = name.split("(")[0].strip()

    # Open world / vendor — no quest gate
    if base in OPEN_WORLD_WEAPONS:
        return "🌍 Open World"
    if not mission.strip() or mission.upper() in ("N/A", "-", ""):
        return "🌍 Open World"

    # Match mission text against our lookup table
    required_ids: list[str] = []
    for fragment, ids in MISSION_TO_IDS.items():
        if fragment.lower() in mission.lower():
            required_ids = ids
            break

    extra_facts = WEAPON_EXTRA_FACTS.get(base, [])

    # If nothing matched but there's a mission listed
    if not required_ids and not extra_facts:
        return "❓ Check Manually"

    quest_ok = all(qid in finished for qid in required_ids) if required_ids else True
    facts_ok  = all(f in facts     for f in extra_facts)    if extra_facts else True

    if quest_ok and facts_ok:
        return "✅ Quest Done – Can Loot!"
    return "🔒 Quest Incomplete"


# ── GOOGLE SHEETS AUTH ────────────────────────────────────────────────────────

def get_gc():
    try:
        import gspread
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        sys.exit(
            "[ERR] Missing dependencies. Run:\n"
            "    pip install gspread google-auth-oauthlib"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_FILE.exists():
                sys.exit(
                    f"[ERR] oauth_client.json not found at {OAUTH_FILE}\n"
                    "Follow the SETUP instructions at the top of this script."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return gspread.authorize(creds)


# ── SHEET UPDATES ─────────────────────────────────────────────────────────────

def update_full_list(ws, save: dict) -> None:
    """Add/update a QUEST STATUS column in the Full List sheet."""
    rows = ws.get_all_values()
    if not rows:
        print("[!] Full List sheet is empty – skipping")
        return

    header = rows[0]

    # Locate or create the STATUS column
    if STATUS_COL_HEADER in header:
        status_col = header.index(STATUS_COL_HEADER) + 1   # 1-indexed
        print(f"[i] Updating existing '{STATUS_COL_HEADER}' column ({col_letter(status_col)})")
    else:
        status_col = len(header) + 1
        ws.update_cell(1, status_col, STATUS_COL_HEADER)
        print(f"[i] Created '{STATUS_COL_HEADER}' column ({col_letter(status_col)})")

    try:
        name_col    = header.index("NAME")
        mission_col = header.index("MISSION")
        req_col     = header.index("REQUIREMENT/CONDITION")
    except ValueError as e:
        print(f"[!] Could not find expected column: {e} – skipping Full List update")
        return

    # Build a 2-D list for the entire status column (rows 2 onward)
    status_values: list[list[str]] = []
    can_loot_count = 0
    for row in rows[1:]:
        name    = row[name_col]    if name_col    < len(row) else ""
        mission = row[mission_col] if mission_col < len(row) else ""
        req     = row[req_col]     if req_col     < len(row) else ""
        if not name:
            status_values.append([""])
            continue
        status = weapon_status(name, mission, req,
                               save["finished_quests"], save["active_facts"])
        if "Can Loot" in status:
            can_loot_count += 1
        status_values.append([status])

    # Single batch write
    start = f"{col_letter(status_col)}2"
    end   = f"{col_letter(status_col)}{len(rows)}"
    ws.update(f"{start}:{end}", status_values)
    print(f"[✓] Wrote {len(status_values)} status cells  ({can_loot_count} ready to loot)")


def update_progress_tab(spreadsheet, save: dict) -> None:
    """Create or overwrite the '📊 My Progress' sheet with player stats."""
    TAB = "📊 My Progress"
    try:
        ws = spreadsheet.worksheet(TAB)
        ws.clear()
    except Exception:
        ws = spreadsheet.add_worksheet(title=TAB, rows=50, cols=4)
        print(f"[i] Created '{TAB}' tab")

    finished = save["finished_quests"]
    facts    = save["active_facts"]
    attrs    = save["attributes"]

    # Count weapons accessible in this save
    full_ws = spreadsheet.worksheet("Full List")
    all_rows = full_ws.get_all_values()
    header = all_rows[0] if all_rows else []
    can_loot = 0
    total_weapons = 0
    if "NAME" in header and "MISSION" in header:
        ni = header.index("NAME")
        mi = header.index("MISSION")
        ri = header.index("REQUIREMENT/CONDITION") if "REQUIREMENT/CONDITION" in header else -1
        for row in all_rows[1:]:
            name = row[ni] if ni < len(row) else ""
            if not name:
                continue
            total_weapons += 1
            mission = row[mi] if mi < len(row) else ""
            req     = row[ri] if ri != -1 and ri < len(row) else ""
            if "Can Loot" in weapon_status(name, mission, req, finished, facts):
                can_loot += 1

    rows_data = [
        # Title
        ["CYBERPUNK 2077 – MY PROGRESS", "", "", ""],
        ["Last updated from save", save["timestamp"], "", ""],
        ["", "", "", ""],

        # Player stats
        ["── PLAYER ──────────────────", "", "", ""],
        ["Level",           save["level"],         "Street Cred",  save["street_cred"]],
        ["Life Path",       save["life_path"],      "Difficulty",   save["difficulty"]],
        ["Play Time",       save["play_time"],      "Game Patch",   save["build_patch"]],
        ["Phantom Liberty", "Yes" if save["has_ep1"] else "No",
                            "Modded",               "Yes" if save["is_modded"] else "No"],
        ["", "", "", ""],

        # Attributes
        ["── ATTRIBUTES ──────────────", "", "", ""],
        ["Body",             attrs["Body"],               "Technical Ability", attrs["Technical Ability"]],
        ["Intelligence",     attrs["Intelligence"],       "Cool",              attrs["Cool"]],
        ["Reflexes",         attrs["Reflexes"],           "", ""],
        ["", "", "", ""],

        # Quest counts
        ["── QUESTS COMPLETED ────────", "", "", ""],
        ["Main Quests  (mq*)",    sum(1 for q in finished if q.startswith("mq")),  "", ""],
        ["Side Jobs    (sq*)",    sum(1 for q in finished if q.startswith("sq")),  "", ""],
        ["Story Quests (q*)",     sum(1 for q in finished if re.match(r"^q\d", q)), "", ""],
        ["Street Stories (sts*)", sum(1 for q in finished if q.startswith("sts")), "", ""],
        ["Minor Activities (ma*)",sum(1 for q in finished if q.startswith("ma")),  "", ""],
        ["Total",                 len(finished),                                    "", ""],
        ["", "", "", ""],

        # Iconic weapons
        ["── ICONIC WEAPONS ──────────", "", "", ""],
        ["Quest Done – Can Loot", can_loot,      "", ""],
        ["Total Tracked",         total_weapons, "", ""],
        ["", "", "", ""],

        # Notable choices / flags
        ["── NOTABLE CHOICES ─────────", "", "", ""],
        ["Romanced Judy",        "Yes" if "sq030_judy_lover"       in facts else "No", "", ""],
        ["River Ward – saved",   "Yes" if "sq012_fact_warn_river"  in facts else "No", "", ""],
        ["Royce killed",         "Yes" if "q003_royce_dead"        in facts else "No", "", ""],
        ["Helped Panam",         "Yes" if "q103_helped_panam"      in facts else "No", "", ""],
        ["Voodoo Queen dead",    "Yes" if "q110_voodoo_queen_dead" in facts else "No", "", ""],
        ["Meredith contract won","Yes" if "q003_meredith_won"      in facts else "No", "", ""],
        ["Phantom Liberty active","Yes" if "ep1_side_content"      in facts else "No", "", ""],
    ]

    ws.update("A1", rows_data)

    # Formatting
    ws.format("A1", {"textFormat": {"bold": True, "fontSize": 14}})
    ws.format("A4,A10,A15,A22,A26",
              {"textFormat": {"bold": True},
               "backgroundColor": {"red": 0.13, "green": 0.13, "blue": 0.13}})

    print(f"[✓] '{TAB}' tab written  ({can_loot}/{total_weapons} weapons accessible)")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync Cyberpunk 2077 save data → Google Sheets tracker"
    )
    parser.add_argument(
        "--save", metavar="FOLDER",
        help="Save folder name (e.g. AutoSave-11). Default: newest save."
    )
    args = parser.parse_args()

    # 1. Load & parse save
    raw  = load_latest_save(args.save)
    save = parse_save(raw)
    print(f"[✓] Save loaded: Level {save['level']}  |  "
          f"Street Cred {save['street_cred']}  |  {save['play_time']} played")

    # 2. Authenticate with Google
    print("[i] Authenticating with Google…")
    gc = get_gc()

    # 3. Open spreadsheet
    spreadsheet = gc.open_by_key(SHEET_ID)
    print(f"[✓] Opened spreadsheet: {spreadsheet.title}")

    # 4. Update Full List status column
    full_list = spreadsheet.worksheet("Full List")
    update_full_list(full_list, save)

    # 5. Update / create My Progress tab
    update_progress_tab(spreadsheet, save)

    print(f"\n[✓] Done!  View your sheet:")
    print(f"    https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()

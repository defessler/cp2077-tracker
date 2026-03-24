#!/usr/bin/env python3
"""
tracker_local.py  ·  Cyberpunk 2077 100% Completion Tracker
=============================================================
Reads your most recent save and generates a local HTML dashboard
tracking every major content category towards 100% completion.

No pip dependencies required. Uses CyberpunkPythonHacks (tools/) for richer
sav.dat fact parsing when available; falls back to metadata.json otherwise.

USAGE
──────
    python tracker_local.py                  # newest save, open browser
    python tracker_local.py --save QuickSave-3
    python tracker_local.py --no-open        # generate file, don't open
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

# ── CONFIG ─────────────────────────────────────────────────────────────────────
SAVE_ROOT    = Path(r"C:\Users\defes\Saved Games\CD Projekt Red\Cyberpunk 2077")
OUTPUT_FILE  = Path(__file__).parent / "tracker_dashboard.html"

# ── QUEST CATALOG ──────────────────────────────────────────────────────────────
# Each category: id, label, color, tags, quests[]
# Each quest: id (matches save's finishedQuests entry), name, tags[]
# tags are searchable chips shown on each quest row

QUEST_CATALOG = [

  # ── MAIN STORY ───────────────────────────────────────────────────────────────
  {
    "id": "main_story", "label": "Main Story", "color": "#00d4ff", "icon": "◈",
    "tags": ["main-story"],
    "quests": [
      # PROLOGUE — one life path applies per playthrough; all share the Watson missions
      {"id": "q000_corpo",       "name": "The Corpo-Rat",         "dep": "life path",                    "check_id": "q000", "tags": ["prologue", "corpo"]},
      {"id": "q000_nomad",       "name": "The Nomad",             "dep": "life path",                    "check_id": "q000", "tags": ["prologue", "nomad"]},
      {"id": "q000_street_kid",  "name": "The Streetkid",         "dep": "life path",                    "check_id": "q000", "tags": ["prologue", "street-kid"]},
      {"id": "q000_tutorial",    "name": "Practice Makes Perfect","dep": "after life path",               "check_id": "q000", "tags": ["prologue"]},
      {"id": "q001_intro",       "name": "The Rescue",            "dep": "after Practice Makes Perfect",  "check_id": "q001", "tags": ["prologue"]},
      {"id": "q001_01_victor",   "name": "The Ripperdoc",         "dep": "after The Rescue",              "check_id": "q001", "tags": ["prologue"]},
      {"id": "q001_02_dex",      "name": "The Ride",              "dep": "after The Ripperdoc",           "check_id": "q001", "tags": ["prologue"]},
      # ACT 1 — The Heist build-up
      {"id": "q003",   "name": "The Pickup",                              "dep": "after Practice Makes Perfect", "tags": ["act1"]},
      {"id": "q004",   "name": "The Information",                         "dep": "parallel with The Pickup","tags": ["act1"]},
      {"id": "q005",   "name": "The Heist",                               "dep": "after The Pickup + The Information", "tags": ["act1"]},
      # INTERLUDE / ACT 2
      {"id": "q101_01_firestorm", "name": "Love Like Fire",       "dep": "after The Heist (Johnny interlude)", "check_id": "q101", "tags": ["act2", "johnny"]},
      {"id": "q101",              "name": "Playing for Time",     "dep": "after Love Like Fire (wakes V)",     "tags": ["act2"]},
      # Judy / Clouds chain (parallel with Panam & Takemura chains)
      {"id": "q105_dollhouse",           "name": "Automatic Love",             "dep": "Playing for Time",               "check_id": "q105", "tags": ["act2", "judy"]},
      {"id": "q105_02_jigjig",           "name": "The Space in Between",       "dep": "after Automatic Love",           "check_id": "q105", "tags": ["act2", "judy"]},
      {"id": "q105_03_braindance_studio","name": "Disasterpiece",              "dep": "after The Space in Between",     "check_id": "q105", "tags": ["act2", "judy"]},
      {"id": "q105_04_judys",            "name": "Double Life",                "dep": "after Disasterpiece",            "check_id": "q105", "tags": ["act2", "judy"]},
      {"id": "q110_voodoo",              "name": "I Walk the Line",            "dep": "after Double Life",              "check_id": "q110", "tags": ["act2", "voodoo-boys"]},
      {"id": "q110_01_voodooboys",       "name": "M'ap Tann Pèlen",            "dep": "after I Walk the Line",          "check_id": "q110", "tags": ["act2", "voodoo-boys"]},
      {"id": "q110_03_cyberspace",       "name": "Transmission",               "dep": "after M'ap Tann Pèlen",          "check_id": "q110", "tags": ["act2", "voodoo-boys"]},
      {"id": "q108",                     "name": "Never Fade Away",            "dep": "plays during Transmission",      "tags": ["act2", "johnny"]},
      # Panam / Nomad chain (parallel)
      {"id": "q103",                     "name": "Ghost Town",                 "dep": "Playing for Time",               "tags": ["act2", "panam"]},
      {"id": "q104_01_sabotage",         "name": "Lightning Breaks",           "dep": "after Ghost Town",               "check_id": "q104", "tags": ["act2", "panam"]},
      {"id": "q104_02_av_chase",         "name": "Life During Wartime",        "dep": "after Lightning Breaks",         "check_id": "q104", "tags": ["act2", "panam"]},
      # Takemura chain (parallel; Play It Safe also needs Life During Wartime)
      {"id": "q112_01_old_friend",       "name": "Down on the Street",         "dep": "Playing for Time",               "check_id": "q112", "tags": ["act2", "takemura"]},
      {"id": "q112_02_industrial_park",  "name": "Gimme Danger",               "dep": "after Down on the Street",       "check_id": "q112", "tags": ["act2", "takemura"]},
      {"id": "q112_03_dashi_parade",     "name": "Play It Safe",               "dep": "after Gimme Danger (+ Life During Wartime)", "check_id": "q112", "tags": ["act2", "takemura"]},
      {"id": "q112_04_hideout",          "name": "Search and Destroy",         "dep": "after Play It Safe",             "check_id": "q112", "tags": ["act2", "takemura"]},
      # ACT 3 — point of no return
      {"id": "q111",   "name": "Nocturne Op55N1",                         "dep": "after all Act 2 chains (point of no return)", "tags": ["act3"]},
      {"id": "q113_rescuing_hanako",     "name": "Last Caress",                "dep": "Nocturne Op55N1: Hanako path",   "check_id": "q113", "tags": ["act3", "hanako"]},
      {"id": "q113_corpo",               "name": "Totalimmortal",              "dep": "after Last Caress",              "check_id": "q113", "tags": ["act3", "hanako"]},
      {"id": "q114_01_nomad_initiation", "name": "We Gotta Live Together",     "dep": "Nocturne Op55N1: Nomad path (+ Queen of the Highway)", "check_id": "q114", "tags": ["act3", "panam"]},
      {"id": "q114_02_maglev_line_assault","name": "Forward to Death",         "dep": "after We Gotta Live Together",   "check_id": "q114", "tags": ["act3", "panam"]},
      {"id": "q114_03_attack_on_arasaka_tower","name": "Belly of the Beast",   "dep": "after Forward to Death",         "check_id": "q114", "tags": ["act3", "panam"]},
      {"id": "q115_afterlife",           "name": "For Whom the Bell Tolls",    "dep": "Nocturne Op55N1: Rogue path (+ Chippin' In)", "check_id": "q115", "tags": ["act3"]},
      {"id": "q115_rogues_last_flight",  "name": "Knockin' on Heaven's Door",  "dep": "after For Whom the Bell Tolls",  "check_id": "q115", "tags": ["act3"]},
      {"id": "q116",   "name": "Changes",                                 "dep": "any Act 3 path",          "tags": ["act3", "ending"]},
      # ENDINGS — complete any one
      {"id": "q201",   "name": "Ending: Where is My Mind? (Hanako)",      "dep": "Last Caress path",        "tags": ["ending", "hanako"]},
      {"id": "q202",   "name": "Ending: All Along the Watchtower (Nomad)","dep": "Belly of the Beast path", "tags": ["ending", "panam"]},
      {"id": "q203",   "name": "Ending: Path of Glory (Johnny/Rogue)",    "dep": "Knockin' on Heaven's Door path", "tags": ["ending", "johnny", "rogue"]},
      {"id": "q204",   "name": "Ending: New Dawn Fades (Arasaka)",        "dep": "Changes path",            "tags": ["ending"]},
      {"id": "q205",   "name": "Ending: Don't Fear the Reaper (Secret)",  "dep": "requires 70%+ Johnny affinity + all Tapeworm phases", "tags": ["ending", "johnny"]},
    ],
  },

  # ── SIDE JOBS ─────────────────────────────────────────────────────────────────
  {
    "id": "side_jobs", "label": "Side Jobs", "color": "#f0e040", "icon": "◇",
    "tags": ["side-job"],
    "quests": [
      # Prologue / very early
      {"id": "sq_q001_wilson",  "name": "The Gun",                              "dep": "after The Rescue (Wilson's shop)",    "tags": ["watson"]},
      {"id": "sq_q001_wakako", "name": "The Gig",                              "dep": "after The Rescue",                    "tags": ["watson"]},
      {"id": "sq018",          "name": "Heroes (Jackie memorial)",             "dep": "after The Heist",                     "tags": ["watson", "jackie"]},
      # Act 2 — unlock from Playing for Time onward
      {"id": "mq025",          "name": "Beat on the Brat",                     "dep": "Act 2, coach Fred in Watson",         "tags": ["combat", "boxing"]},
      {"id": "sq025",          "name": "Epistrophy (Delamain cabs)",           "dep": "Playing for Time, Delamain calls",    "tags": ["delamain", "driving"]},
      {"id": "sq006",          "name": "Dream On",                             "dep": "Act 2, apartment call",               "tags": ["westbrook"]},
      {"id": "sq012",          "name": "I Fought the Law",                     "dep": "Act 2",                               "tags": ["ncpd", "heywood"]},
      {"id": "sq021",          "name": "The Hunt",                             "dep": "Act 2",                               "tags": ["river", "ncpd"]},
      {"id": "sq024_badlands_race",      "name": "The Beast in Me: Badlands",      "dep": "Act 2",                        "check_id": "sq024", "tags": ["racing", "claire", "badlands"]},
      {"id": "sq024_city_race",         "name": "The Beast in Me: City Center",  "dep": "Act 2",                        "check_id": "sq024", "tags": ["racing", "claire", "city-center"]},
      {"id": "sq024_santo_domingo_race","name": "The Beast in Me: Santo Domingo","dep": "Act 2",                        "check_id": "sq024", "tags": ["racing", "claire", "santo-domingo"]},
      {"id": "sq024_the_big_race",      "name": "The Beast in Me: The Big Race", "dep": "after all 3 Claire races",    "check_id": "sq024", "tags": ["racing", "claire"]},
      {"id": "sq023_hit_order",         "name": "Sinnerman",                            "dep": "Act 2",                  "check_id": "sq023", "tags": ["pacifica"]},
      {"id": "sq023_bd_passion",        "name": "There Is A Light That Never Goes Out", "dep": "after Sinnerman",        "check_id": "sq023", "tags": ["pacifica"]},
      {"id": "sq023_real_passion",      "name": "They Won't Go When I Go",              "dep": "after There Is A Light", "check_id": "sq023", "tags": ["pacifica"]},
      # Panam side chain (dep: Life During Wartime → Riders on the Storm → With a Little Help)
      {"id": "sq004",          "name": "Riders on the Storm",                  "dep": "after Life During Wartime (~12hr wait)","tags": ["panam", "badlands"]},
      {"id": "sq027_01_basilisk_convoy",    "name": "With a Little Help from My Friends", "dep": "after Riders on the Storm", "check_id": "sq027", "tags": ["panam", "nomads"]},
      {"id": "sq027_02_raffen_shiv_attack", "name": "Queen of the Highway",             "dep": "after With a Little Help",  "check_id": "sq027", "tags": ["panam", "nomads"]},
      # Judy side chain (dep: Double Life main quest)
      {"id": "sq026_01_suicide","name": "Both Sides, Now",                "dep": "after Double Life",                  "check_id": "sq026", "tags": ["judy"]},
      {"id": "sq026_02_maiko",  "name": "Ex-Factor",                      "dep": "after Both Sides, Now",              "check_id": "sq026", "tags": ["judy"]},
      {"id": "sq026_03_pizza",  "name": "Talkin' 'bout a Revolution",     "dep": "after Ex-Factor",                    "check_id": "sq026", "tags": ["judy"]},
      {"id": "sq026_04_hiromi", "name": "Pisces",                         "dep": "after Talkin' 'bout a Revolution",   "check_id": "sq026", "tags": ["judy"]},
      # River romance chain (dep: The Hunt)
      {"id": "sq029",          "name": "Following the River",                  "dep": "after The Hunt",                      "tags": ["river", "romance"]},
      # Late Act 2 — Tapeworm phases trigger from Automatic Love → Transmission → Life During Wartime → Search & Destroy
      {"id": "sq032",          "name": "Tapeworm",                             "dep": "all 4 phases across Act 2 main quests","tags": ["johnny"]},
      {"id": "sq031_smack_my_bitch_up", "name": "A Cool Metal Fire", "dep": "after Tapeworm (Automatic Love phase)",  "check_id": "sq031", "tags": ["johnny"]},
      {"id": "sq031_rogue",             "name": "Chippin' In",        "dep": "after all Tapeworm phases",              "check_id": "sq031", "tags": ["johnny", "rogue"]},
      {"id": "sq031_cinema",            "name": "Blistering Love",    "dep": "after Chippin' In",                      "check_id": "sq031", "tags": ["johnny", "rogue"]},
      # Kerry chain (dep: Chippin' In → A Like Supreme → Second Conflict → Holdin' On → Boat Drinks)
      {"id": "sq011_concert",  "name": "A Like Supreme",   "dep": "after Chippin' In",           "check_id": "sq011", "tags": ["kerry", "samurai", "music"]},
      {"id": "sq011_johnny",   "name": "Second Conflict",  "dep": "after A Like Supreme",        "check_id": "sq011", "tags": ["kerry", "johnny", "music"]},
      {"id": "sq011_kerry",    "name": "Holdin' On",        "dep": "after Second Conflict",       "check_id": "sq011", "tags": ["kerry", "music"]},
      {"id": "sq017_kerry",     "name": "Rebel! Rebel!",         "dep": "after A Like Supreme",           "check_id": "sq017", "tags": ["kerry", "westbrook"]},
      {"id": "sq017_01_riot_club","name": "I Don't Wanna Hear It","dep": "after Rebel! Rebel!",            "check_id": "sq017", "tags": ["kerry", "westbrook"]},
      {"id": "sq017_02_lounge", "name": "Off the Leash",          "dep": "after I Don't Wanna Hear It",   "check_id": "sq017", "tags": ["kerry", "westbrook"]},
      {"id": "sq028_kerry_romance", "name": "Boat Drinks",        "dep": "after Holdin' On (Kerry romance)","check_id": "sq028", "tags": ["kerry", "romance"]},
      # Judy romance finale (dep: Pisces from Judy side chain)
      {"id": "sq030",          "name": "Pyramid Song",                         "dep": "after Pisces (Judy side chain)",       "tags": ["judy", "underwater"]},
    ],
  },

  # ── PHANTOM LIBERTY — MAIN ───────────────────────────────────────────────────
  {
    "id": "phantom_liberty", "label": "Phantom Liberty", "color": "#cc66ff", "icon": "◉",
    "tags": ["phantom-liberty", "dlc"],
    "quests": [
      # Completed
      {"id": "q300",   "name": "Phantom Liberty (opener)",                        "tags": ["pl-main"]},
      {"id": "q301_crash",              "name": "Dog Eat Dog",            "dep": "after Phantom Liberty",              "check_id": "q301", "tags": ["pl-main", "myers"]},
      {"id": "q301_finding_myers",      "name": "Hole in the Sky",        "dep": "after Dog Eat Dog",                  "check_id": "q301", "tags": ["pl-main", "myers", "songbird"]},
      {"id": "q301_q302_rescue_myers",  "name": "Spider and the Fly",     "dep": "after Hole in the Sky",              "check_id": "q302", "tags": ["pl-main", "myers"]},
      {"id": "q302",                    "name": "Lucretia My Reflection",  "dep": "after Spider and the Fly",                               "tags": ["pl-main", "reed"]},
      {"id": "q303_baron",         "name": "The Damned",                   "dep": "after Lucretia My Reflection",       "check_id": "q303", "tags": ["pl-main"]},
      {"id": "q303_hands",         "name": "Get It Together",              "dep": "after The Damned",                   "check_id": "q303", "tags": ["pl-main"]},
      {"id": "q303_songbird",      "name": "You Know My Name",             "dep": "after Get It Together",              "check_id": "q303", "tags": ["pl-main", "songbird"]},
      {"id": "q304_deal",          "name": "Firestarter",                  "dep": "after You Know My Name",             "check_id": "q304", "tags": ["pl-main"]},
      {"id": "q304_netrunners",    "name": "I've Seen That Face Before",   "dep": "after Firestarter",                  "check_id": "q304", "tags": ["pl-main", "songbird"]},
      {"id": "q304_stadium",       "name": "Birds with Broken Wings",      "dep": "after I've Seen That Face Before",   "check_id": "q304", "tags": ["pl-main"]},
      # Branches after Birds with Broken Wings — Reed or Songbird path
      # Reed path — check q305_done fact (set when chain completes)
      {"id": "q305_prison_convoy",  "name": "Black Steel in the Hour of Chaos", "dep": "Birds with Broken Wings: Reed path",    "check_fact": "q305_done", "tags": ["pl-main", "reed"]},
      {"id": "q305_bunker",         "name": "Somewhat Damaged",                 "dep": "after Black Steel (Reed path)",         "check_fact": "q305_done", "tags": ["pl-main", "reed"]},
      {"id": "q305_postcontent",    "name": "This Corrosion",                   "dep": "after Somewhat Damaged (Reed path)",    "check_fact": "q305_done", "tags": ["pl-main", "reed"]},
      {"id": "q305_reed_epilogue",  "name": "Four Score and Seven",             "dep": "Reed path finale",                      "check_fact": "q305_done", "tags": ["pl-main", "ending", "reed"]},
      {"id": "q306_postcontent",    "name": "From Her to Eternity",             "dep": "Four Score and Seven (Reed path)",      "check_fact": "q306_done", "tags": ["pl-main", "ending", "reed"]},
      {"id": "q306_reed_epilogue",  "name": "Through Pain to Heaven",           "dep": "From Her to Eternity (Reed path)",      "check_fact": "q306_done", "tags": ["pl-main", "ending", "reed"]},
      # Songbird path — check q306_done fact
      {"id": "q305_border_crossing","name": "Leave in Silence",                 "dep": "Birds with Broken Wings: Songbird path","check_fact": "q305_done", "tags": ["pl-main", "songbird"]},
      {"id": "q306_devils_bargain", "name": "The Killing Moon",                 "dep": "after Leave in Silence (Songbird path)","check_fact": "q306_done", "tags": ["pl-main", "ending", "songbird"]},
      {"id": "q306_somi_epilogue",  "name": "Unfinished Sympathy",              "dep": "after The Killing Moon (Songbird path)","check_fact": "q306_done", "tags": ["pl-main", "ending", "songbird"]},
      # Shared epilogue — check q307_done fact
      {"id": "q307_tomorrow",       "name": "Things Done Changed",              "dep": "The Killing Moon path",                 "check_fact": "q307_done", "tags": ["pl-main", "ending"]},
      {"id": "q307_before_tomorrow","name": "Who Wants to Live Forever",        "dep": "From Her to Eternity path",             "check_fact": "q307_done", "tags": ["pl-main", "ending"]},
      # PL minor side quests
      {"id": "mq303",  "name": "Dazed and Confused",                              "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq305",  "name": "Shot by Both Sides",                              "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq306",  "name": "No Easy Way Out",                                 "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq301",  "name": "Balls to the Wall",                               "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
    ],
  },

  # ── PHANTOM LIBERTY — SIDE CONTENT ───────────────────────────────────────────
  {
    "id": "pl_side", "label": "PL Side Quests & Activities", "color": "#9966ff", "icon": "◈",
    "tags": ["phantom-liberty", "dlc", "side-job"],
    "quests": [
      {"id": "wst_ep1_04",    "name": "Addicted to Chaos",              "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_05",    "name": "Go Your Own Way",                "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_11",    "name": "New Person, Same Old Mistakes",  "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_21",    "name": "Water Runs Dry",                 "tags": ["dogtown", "pl-side"]},
      {"id": "we_ep1_01",     "name": "Balls to the Wall",              "tags": ["dogtown", "pl-side"]},
      {"id": "we_ep1_05",     "name": "Run This Town",                  "tags": ["dogtown", "pl-side"]},
      {"id": "sa_ep1_courier","name": "Courier Quests",                 "tags": ["dogtown", "pl-side"]},
      {"id": "cbj_ep1_02",    "name": "Bounty Job #2",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_03",    "name": "Bounty Job #3",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_04",    "name": "Bounty Job #4",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_05",    "name": "Bounty Job #5",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_06",    "name": "Bounty Job #6",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_07",    "name": "Bounty Job #7",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_08",    "name": "Bounty Job #8",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_09",    "name": "Bounty Job #9",                  "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_10",    "name": "Bounty Job #10",                 "tags": ["dogtown", "bounty", "pl-side"]},
      {"id": "cbj_ep1_11",    "name": "Bounty Job #11",                 "tags": ["dogtown", "bounty", "pl-side"]},
    ],
  },

  # ── MINOR ACTIVITIES ──────────────────────────────────────────────────────────
  {
    "id": "minor_activities", "label": "Minor Activities", "color": "#888899", "icon": "◌",
    "tags": ["minor"],
    "quests": [
      # Early / Act 1
      {"id": "mq002",  "name": "Gun Music",                                "dep": "Act 1, Watson",            "tags": ["minor", "watson"]},
      {"id": "mq003",  "name": "Space Oddity",                             "dep": "Act 1",                    "tags": ["minor"]},
      {"id": "mq005",  "name": "Only Pain",                                "dep": "Act 1",                    "tags": ["minor"]},
      {"id": "mq006",  "name": "Love Rollercoaster",                       "dep": "Act 1",                    "tags": ["minor"]},
      {"id": "mq007",  "name": "Machine Gun",                              "dep": "Act 1",                    "tags": ["minor"]},
      {"id": "mq008",  "name": "Stadium Love",                             "dep": "Act 1",                    "tags": ["minor"]},
      # Act 2
      {"id": "mq001",  "name": "I'll Fly Away",                            "dep": "during Panam Act 2 chain", "tags": ["minor", "panam"]},
      {"id": "mq010",  "name": "Happy Together",                           "dep": "Act 2, Megabuilding H4",   "tags": ["minor", "watson"]},
      {"id": "mq011",  "name": "Shoot to Thrill",                          "dep": "Act 2, Watson",            "tags": ["minor", "watson"]},
      {"id": "mq012",  "name": "Burning Desire",                           "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq013",  "name": "A Day in the Life",                        "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq014",  "name": "Sacrum Profanum (tarot readings)",         "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq015",  "name": "Spellbound",                               "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq016",  "name": "KOLD MIRAGE",                              "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq017",  "name": "Small Man, Big Mouth",                     "dep": "Act 2",                    "tags": ["minor", "street-kid"]},
      {"id": "mq018",  "name": "Killing In The Name",                      "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq019",  "name": "Violence",                                 "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq021",  "name": "Fortunate Son",                            "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq022",  "name": "Ezekiel Saw the Wheel",                    "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq023",  "name": "The Ballad of Buck Ravers",                "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq024",  "name": "Full Disclosure",                          "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq026",  "name": "The Prophet's Song",                       "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq027",  "name": "Living on the Edge",                       "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq028",  "name": "Every Breath You Take",                    "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq029",  "name": "The Highwayman",                           "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq030",  "name": "Bullets",                                  "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq032",  "name": "Sacrum Profanum",                          "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq033",  "name": "Fool on the Hill",                         "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq035",  "name": "Send in the Clowns",                       "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq036",  "name": "Sweet Dreams",                             "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq037",  "name": "Coin Operated Boy",                        "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq038",  "name": "Big in Japan",                             "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq040",  "name": "Raymond Chandler Evening",                 "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq041",  "name": "War Pigs",                                 "dep": "Act 2",                    "tags": ["minor", "corpo"]},
      {"id": "mq042",  "name": "These Boots Are Made for Walkin'",         "dep": "Act 2",                    "tags": ["minor", "nomad"]},
      {"id": "mq043",  "name": "Psycho Killer",                            "dep": "after all 17 cyberpsychos","tags": ["minor", "cyberpsycho"]},
      {"id": "mq044",  "name": "Sex on Wheels",                            "dep": "Act 2",                    "tags": ["minor", "vehicle"]},
      {"id": "mq045",  "name": "Paid in Full",                             "dep": "Act 2, pay Victor",        "tags": ["minor"]},
      {"id": "mq046",  "name": "Murk Man Returns Again Once More Forever", "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq047",  "name": "Dressed to Kill",                          "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq048",  "name": "Upgrade U",                                "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq049",  "name": "Over the Edge",                            "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq050",  "name": "I'm in Love with My Car",                  "dep": "Act 2",                    "tags": ["minor", "vehicle"]},
      {"id": "mq055",  "name": "I Really Want to Stay at Your House",      "dep": "Act 2, romance",           "tags": ["minor", "romance"]},
      {"id": "mq056",  "name": "The Distance",                             "dep": "Act 2",                    "tags": ["minor", "racing"]},
      {"id": "mq057",  "name": "Motorbreath",                              "dep": "Act 2",                    "tags": ["minor", "racing"]},
      {"id": "mq058",  "name": "Where Eagles Dare",                        "dep": "Act 2",                    "tags": ["minor", "vehicle"]},
      {"id": "mq059",  "name": "Freedom",                                  "dep": "Act 2",                    "tags": ["minor"]},
      {"id": "mq060",  "name": "Nitro",                                    "dep": "Act 2",                    "tags": ["minor"]},
    ],
  },

  # ── GIGS — WATSON ─────────────────────────────────────────────────────────────
  {
    "id": "gigs_watson", "label": "Gigs — Watson", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "watson"],
    "quests": [
      {"id": "sts_wat_kab_01",  "name": "Concrete Cage Trap",           "tags": ["kabuki"]},
      {"id": "sts_wat_kab_02",  "name": "Hippocratic Oath",             "tags": ["kabuki"]},
      {"id": "sts_wat_kab_03",  "name": "Backs Against the Wall",       "tags": ["kabuki"]},
      {"id": "sts_wat_kab_04",  "name": "Fixer, Merc, Soldier, Spy",    "tags": ["kabuki"]},
      {"id": "sts_wat_kab_05",  "name": "Last Login",                   "tags": ["kabuki"]},
      {"id": "sts_wat_kab_06",  "name": "Shark in the Water",           "tags": ["kabuki"]},
      {"id": "sts_wat_kab_07",  "name": "Monster Hunt",                 "tags": ["kabuki"]},
      {"id": "sts_wat_kab_08",  "name": "Woman of La Mancha",           "tags": ["kabuki"]},
      {"id": "sts_wat_kab_101", "name": "Small Man, Big Evil",          "tags": ["kabuki"]},
      {"id": "sts_wat_kab_102", "name": "Welcome to America, Comrade",  "tags": ["kabuki"]},
      {"id": "sts_wat_kab_107", "name": "Troublesome Neighbors",        "tags": ["kabuki"]},
      {"id": "sts_wat_lch_01",  "name": "Catch a Tyger's Toe",          "tags": ["little-china"]},
      {"id": "sts_wat_lch_03",  "name": "Bloodsport",                   "tags": ["little-china"]},
      {"id": "sts_wat_lch_05",  "name": "Playing for Keeps",            "tags": ["little-china"]},
      {"id": "sts_wat_lch_06",  "name": "The Heisenberg Principle",     "tags": ["little-china"]},
      {"id": "sts_wat_nid_01",  "name": "Occupational Hazard",          "tags": ["northside"]},
      {"id": "sts_wat_nid_02",  "name": "Many Ways to Skin a Cat",      "tags": ["northside"]},
      {"id": "sts_wat_nid_03",  "name": "Flight of the Cheetah",        "tags": ["northside"]},
      {"id": "sts_wat_nid_04",  "name": "Dirty Biz",                    "tags": ["northside"]},
      {"id": "sts_wat_nid_05",  "name": "Rite of Passage",              "tags": ["northside"]},
      {"id": "sts_wat_nid_06",  "name": "Lousy Kleppers",               "tags": ["northside"]},
      {"id": "sts_wat_nid_07",  "name": "Scrolls Before Swine",         "tags": ["northside"]},
      {"id": "sts_wat_nid_12",  "name": "Freedom of the Press",         "tags": ["northside"]},
    ],
  },

  # ── GIGS — WESTBROOK ──────────────────────────────────────────────────────────
  {
    "id": "gigs_westbrook", "label": "Gigs — Westbrook", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "westbrook"],
    "quests": [
      {"id": "sts_wbr_hil_01",  "name": "Until Death Do Us Part",       "tags": ["north-oak"]},
      {"id": "sts_wbr_hil_06",  "name": "Family Heirloom",              "tags": ["north-oak"]},
      {"id": "sts_wbr_hil_07",  "name": "Tyger and Vulture",            "tags": ["north-oak"]},
      {"id": "sts_wbr_jpn_01",  "name": "Olive Branch",                 "tags": ["japantown"]},
      {"id": "sts_wbr_jpn_02",  "name": "We Have Your Wife",            "tags": ["japantown"]},
      {"id": "sts_wbr_jpn_03",  "name": "A Shrine Defiled",             "tags": ["japantown"]},
      {"id": "sts_wbr_jpn_05",  "name": "Wakako's Favorite",            "tags": ["japantown"]},
      {"id": "sts_wbr_jpn_09",  "name": "Hothead",                      "tags": ["japantown"], "wiki": "Hothead_(gig)"},
      {"id": "sts_wbr_jpn_12",  "name": "Greed Never Pays",             "tags": ["japantown"]},
    ],
  },

  # ── GIGS — CITY CENTER ────────────────────────────────────────────────────────
  {
    "id": "gigs_city_center", "label": "Gigs — City Center", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "city-center"],
    "quests": [
      {"id": "sts_cct_cpz_01",  "name": "Serial Suicide",               "tags": ["corpo-plaza"]},
      {"id": "sts_cct_dtn_02",  "name": "An Inconvenient Killer",       "tags": ["downtown"]},
      {"id": "sts_cct_dtn_03",  "name": "A Lack of Empathy",            "tags": ["downtown"]},
      {"id": "sts_cct_dtn_04",  "name": "Guinea Pigs",                  "tags": ["downtown"]},
      {"id": "sts_cct_dtn_05",  "name": "The Frolics of Councilwoman Cole", "tags": ["downtown"]},
    ],
  },

  # ── GIGS — HEYWOOD ────────────────────────────────────────────────────────────
  {
    "id": "gigs_heywood", "label": "Gigs — Heywood", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "heywood"],
    "quests": [
      {"id": "sts_hey_gle_01",  "name": "Eye for an Eye",               "tags": ["the-glen"]},
      {"id": "sts_hey_gle_03",  "name": "Psychofan",                    "tags": ["the-glen"]},
      {"id": "sts_hey_gle_04",  "name": "Fifth Column",                 "tags": ["the-glen"]},
      {"id": "sts_hey_gle_05",  "name": "Going Up or Down?",            "tags": ["the-glen"]},
      {"id": "sts_hey_gle_06",  "name": "Life's Work",                  "tags": ["the-glen"]},
      {"id": "sts_hey_rey_01",  "name": "Bring Me the Head of Gustavo Orta", "tags": ["vista-del-rey"]},
      {"id": "sts_hey_rey_02",  "name": "Sr. Ladrillo's Private Collection", "tags": ["vista-del-rey"]},
      {"id": "sts_hey_rey_06",  "name": "Jeopardy",                     "tags": ["vista-del-rey"]},
      {"id": "sts_hey_rey_08",  "name": "Old Friends",                  "tags": ["vista-del-rey"]},
      {"id": "sts_hey_rey_09",  "name": "Getting Warmer...",            "tags": ["vista-del-rey"]},
      {"id": "sts_hey_spr_01",  "name": "On a Tight Leash",             "tags": ["wellsprings"]},
      {"id": "sts_hey_spr_03",  "name": "The Lord Giveth and Taketh Away", "tags": ["wellsprings"]},
      {"id": "sts_hey_spr_06",  "name": "Hot Merchandise",              "tags": ["wellsprings"]},
    ],
  },

  # ── GIGS — SANTO DOMINGO ──────────────────────────────────────────────────────
  {
    "id": "gigs_santo_domingo", "label": "Gigs — Santo Domingo", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "santo-domingo"],
    "quests": [
      {"id": "sts_std_arr_01",  "name": "Serious Side Effects",         "tags": ["arroyo"]},
      {"id": "sts_std_arr_03",  "name": "Race to the Top",              "tags": ["arroyo"]},
      {"id": "sts_std_arr_05",  "name": "Breaking News",                "tags": ["arroyo"]},
      {"id": "sts_std_arr_06",  "name": "Nasty Hangover",               "tags": ["arroyo"]},
      {"id": "sts_std_arr_10",  "name": "Severance Package",            "tags": ["arroyo"]},
      {"id": "sts_std_arr_11",  "name": "Hacking the Hacker",           "tags": ["arroyo"]},
      {"id": "sts_std_arr_12",  "name": "Desperate Measures",           "tags": ["arroyo"]},
      {"id": "sts_std_rcr_01",  "name": "The Union Strikes Back",       "tags": ["rancho-coronado"]},
      {"id": "sts_std_rcr_02",  "name": "Cuckoo's Nest",                "tags": ["rancho-coronado"]},
      {"id": "sts_std_rcr_03",  "name": "Going-away Party",             "tags": ["rancho-coronado"]},
      {"id": "sts_std_rcr_04",  "name": "Error 404",                    "tags": ["rancho-coronado"]},
      {"id": "sts_std_rcr_05",  "name": "Family Matters",               "tags": ["rancho-coronado"]},
    ],
  },

  # ── GIGS — BADLANDS & PACIFICA ────────────────────────────────────────────────
  {
    "id": "gigs_outer", "label": "Gigs — Badlands & Pacifica", "color": "#39d353", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "badlands", "pacifica"],
    "quests": [
      {"id": "sts_bls_ina_02",  "name": "Big Pete's Got Big Problems",  "tags": ["badlands"]},
      {"id": "sts_bls_ina_03",  "name": "Flying Drugs",                 "tags": ["badlands"]},
      {"id": "sts_bls_ina_04",  "name": "Radar Love",                   "tags": ["badlands"]},
      {"id": "sts_bls_ina_05",  "name": "Goodbye, Night City",          "tags": ["badlands"]},
      {"id": "sts_bls_ina_06",  "name": "No Fixers",                    "tags": ["badlands"]},
      {"id": "sts_bls_ina_07",  "name": "Dancing on a Minefield",       "tags": ["badlands"]},
      {"id": "sts_bls_ina_08",  "name": "Trevor's Last Ride",           "tags": ["badlands"]},
      {"id": "sts_bls_ina_09",  "name": "MIA",                          "tags": ["badlands"]},
      {"id": "sts_bls_ina_11",  "name": "Sparring Partner",             "tags": ["badlands"]},
      {"id": "sts_pac_cvi_02",  "name": "Two Wrongs Makes Us Right",    "tags": ["pacifica", "coast-view"]},
      {"id": "sts_pac_wwd_05",  "name": "For My Son",                   "tags": ["pacifica", "west-wind"]},
    ],
  },

  # ── GIGS — PHANTOM LIBERTY (DOGTOWN) ─────────────────────────────────────────
  {
    "id": "gigs_dogtown", "label": "Gigs — Dogtown (PL)", "color": "#cc66ff", "icon": "◆",
    "show_wiki": False,
    "tags": ["gig", "dogtown", "phantom-liberty"],
    "quests": [
      {"id": "sts_ep1_01",  "name": "Dogtown Saints",                   "tags": ["dogtown"]},
      {"id": "sts_ep1_03",  "name": "The Man Who Killed Jason Foreman", "tags": ["dogtown"]},
      {"id": "sts_ep1_04",  "name": "Prototype in the Scraper",         "tags": ["dogtown"]},
      {"id": "sts_ep1_06",  "name": "Heaviest of Hearts",               "tags": ["dogtown"]},
      {"id": "sts_ep1_07",  "name": "Roads to Redemption",              "tags": ["dogtown"]},
      {"id": "sts_ep1_08",  "name": "Spy in the Jungle",                "tags": ["dogtown"]},
      {"id": "sts_ep1_10",  "name": "Waiting for Dodger",               "tags": ["dogtown"]},
      {"id": "sts_ep1_12",  "name": "Treating Symptoms",                "tags": ["dogtown"]},
      {"id": "sts_ep1_13",  "name": "Talent Academy",                   "tags": ["dogtown"]},
    ],
  },

  # ── CYBERPSYCHO SIGHTINGS ─────────────────────────────────────────────────────
  {
    "id": "cyberpsychos", "label": "Cyberpsycho Sightings", "color": "#ff4455", "icon": "⚠",
    "show_wiki": False,
    "tags": ["cyberpsycho", "ncpd"],
    "quests": [
      {"id": "ma_wat_kab_02",      "name": "Demons of War",             "tags": ["watson", "kabuki"]},
      {"id": "ma_wat_kab_08",      "name": "Lt. Mower",                 "tags": ["watson", "kabuki"]},
      {"id": "ma_wat_lch_06",      "name": "Ticket to the Major Leagues", "tags": ["watson", "little-china"]},
      {"id": "ma_wat_nid_03",      "name": "Where the Bodies Hit the Floor", "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_15",      "name": "Bloody Ritual",             "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_22",      "name": "Six Feet Under",            "tags": ["watson", "northside"]},
      {"id": "ma_cct_dtn_03",      "name": "On Deaf Ears",              "tags": ["city-center", "downtown"]},
      {"id": "ma_cct_dtn_07",      "name": "Phantom of Night City",     "tags": ["city-center", "downtown"]},
      {"id": "ma_hey_spr_04",      "name": "Seaside Cafe",              "tags": ["heywood", "wellsprings"]},
      {"id": "ma_hey_spr_06",      "name": "Letter of the Law",         "tags": ["heywood", "wellsprings"]},
      {"id": "ma_std_arr_06",      "name": "Under the Bridge",          "tags": ["santo-domingo", "arroyo"]},
      {"id": "ma_std_rcr_11",      "name": "Discount Doc",              "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_pac_cvi_08",      "name": "Smoke on the Water",        "tags": ["pacifica", "coast-view"]},
      {"id": "ma_pac_cvi_15",      "name": "Lex Talionis",              "tags": ["pacifica", "coast-view"]},
      {"id": "ma_bls_ina_se1_07",  "name": "The Wasteland",             "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_08",  "name": "House on a Hill",           "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_22",  "name": "Second Chances",            "tags": ["badlands"]},
    ],
  },

  # ── NCPD REPORTED CRIMES ──────────────────────────────────────────────────────
  {
    "id": "ncpd", "label": "NCPD Reported Crimes", "color": "#ff8833", "icon": "⬡",
    "show_wiki": False,
    "tags": ["ncpd", "reported-crime"],
    "quests": [
      # Watson — Kabuki
      {"id": "ma_wat_kab_05",      "name": "Protect and Serve",                      "tags": ["watson", "kabuki"]},
      {"id": "ma_wat_kab_10",      "name": "Reported Crime: Watson Kabuki",          "tags": ["watson", "kabuki"]},
      # Watson — Little China
      {"id": "ma_wat_lch_01",      "name": "Opposites Attract",                      "tags": ["watson", "little-china"]},
      {"id": "ma_wat_lch_03",      "name": "Worldly Possessions",                    "tags": ["watson", "little-china"]},
      {"id": "ma_wat_lch_05",      "name": "Paranoia",                               "tags": ["watson", "little-china"]},
      {"id": "ma_wat_lch_08",      "name": "Tygers by the Tail",                     "tags": ["watson", "little-china"]},
      {"id": "ma_wat_lch_15",      "name": "Dangerous Currents",                     "tags": ["watson", "little-china"]},
      # Watson — Northside
      {"id": "ma_wat_nid_01",      "name": "Vice Control",                           "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_02",      "name": "Just Say No",                            "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_06",      "name": "No License, No Problem",                 "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_10",      "name": "Dredged Up",                             "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_12",      "name": "Needle in a Haystack",                   "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_26",      "name": "One Thing Led to Another",               "tags": ["watson", "northside"]},
      {"id": "ma_wat_nid_27",      "name": "Don't Forget the Parking Brake!",        "tags": ["watson", "northside"]},
      # Westbrook — North Oak
      {"id": "ma_wbr_hil_05",      "name": "You Play with Fire...",                  "tags": ["westbrook", "north-oak"]},
      {"id": "ma_wbr_nok_01",      "name": "Crash Test",                             "tags": ["westbrook", "north-oak"]},
      {"id": "ma_wbr_nok_03",      "name": "Table Scraps",                           "tags": ["westbrook", "north-oak"]},
      {"id": "ma_wbr_nok_05",      "name": "Privacy Policy Violation",               "tags": ["westbrook", "north-oak"]},
      # Westbrook — Japantown
      {"id": "ma_wbr_jpn_07",      "name": "Lost and Found",                         "tags": ["westbrook", "japantown"]},
      {"id": "ma_wbr_jpn_09",      "name": "Another Circle of Hell",                 "tags": ["westbrook", "japantown"]},
      {"id": "ma_wbr_jpn_16",      "name": "Reported Crime: Westbrook Japantown",    "tags": ["westbrook", "japantown"]},
      {"id": "ma_cct_cpz_06",      "name": "Reported Crime: Corpo Plaza",            "tags": ["city-center", "corpo-plaza"]},
      {"id": "ma_cct_dtn_12",      "name": "Turn Off the Tap",                       "tags": ["city-center", "downtown"]},
      {"id": "ma_hey_gle_02",      "name": "Suspected Org Crime: Chapel",            "tags": ["heywood", "the-glen"]},
      {"id": "ma_hey_gle_07",      "name": "Smoking Kills",                          "tags": ["heywood", "the-glen"]},
      {"id": "ma_hey_rey_05",      "name": "Reported Crime: Vista del Rey",          "tags": ["heywood", "vista-del-rey"]},
      {"id": "ma_hey_spr_11",      "name": "Living the Big Life",                    "tags": ["heywood", "wellsprings"]},
      {"id": "ma_pac_cvi_10",      "name": "Roadside Picnic",                        "tags": ["pacifica", "coast-view"]},
      {"id": "ma_pac_cvi_12",      "name": "Wipe the Gonk, Take the Implants",       "tags": ["pacifica", "coast-view"]},
      {"id": "ma_pac_cvi_13",      "name": "Honey, Where are You?",                  "tags": ["pacifica", "coast-view"]},
      {"id": "ma_std_arr_07",      "name": "Disloyal Employee",                      "tags": ["santo-domingo", "arroyo"]},
      {"id": "ma_std_arr_10",      "name": "Ooh, Awkward",                           "tags": ["santo-domingo", "arroyo"]},
      {"id": "ma_std_arr_11",      "name": "Supply Management",                      "tags": ["santo-domingo", "arroyo"]},
      {"id": "ma_std_arr_14",      "name": "Reported Crime: Arroyo",                 "tags": ["santo-domingo", "arroyo"]},
      {"id": "ma_std_rcr_04",      "name": "Reported Crime: Rancho Coronado",        "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_std_rcr_10",      "name": "Welcome to Night City",                  "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_std_rcr_12",      "name": "A Stroke of Luck",                       "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_std_rcr_13",      "name": "Justice Behind Bars",                    "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_std_rcr_14",      "name": "Reported Crime: Rancho Coronado B",      "tags": ["santo-domingo", "rancho-coronado"]},
      {"id": "ma_bls_ina_se1_02",  "name": "Comrade Red",                            "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_03",  "name": "Blood in the Air",                       "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_06",  "name": "Extremely Loud and Incredibly Close",    "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_13",  "name": "Reported Crime: Badlands",               "tags": ["badlands"]},
      {"id": "ma_bls_ina_se1_18",  "name": "I Don't Like Sand",                      "tags": ["badlands"]},
      {"id": "ma_bls_ina_se5_33",  "name": "Delivery From Above",                    "tags": ["badlands"]},
    ],
  },

  # ── ICONIC WEAPONS ────────────────────────────────────────────────────────────
  {
    "id": "iconic_weapons", "label": "Iconic Weapons", "color": "#f0e040", "icon": "⚔",
    "tags": ["weapon", "iconic"],
    "note": "Click any row to mark as collected — saved in your browser",
    "quests": [
      # These use a special check — see weapon_status() below
      {"id": "_weapon_dying_night",      "name": "Dying Night (Pistol)",          "tags": ["open-world", "watson"]},
      {"id": "_weapon_guts",             "name": "Guts (Shotgun)",                "tags": ["open-world", "arroyo"]},
      {"id": "_weapon_blue_fang",        "name": "Blue Fang (Knife)",             "tags": ["open-world", "kabuki"]},
      {"id": "_weapon_headhunter",       "name": "Headhunter (Revolver)",         "tags": ["open-world"]},
      {"id": "_weapon_skippy",           "name": "Skippy (Smart Pistol)",         "tags": ["open-world", "vista-del-rey"]},
      {"id": "_weapon_comrades_hammer",  "name": "Comrade's Hammer (Revolver)",   "tags": ["open-world", "badlands"]},
      {"id": "_weapon_kongou",           "name": "Kongou (Pistol)",               "tags": ["act1", "the-heist"]},
      {"id": "_weapon_satori",           "name": "Satori (Katana)",               "tags": ["act1", "the-heist"]},
      {"id": "_weapon_chaos",            "name": "Chaos (Pistol)",                "tags": ["act1", "the-pickup", "choice"]},
      {"id": "_weapon_buzzsaw",          "name": "Buzzsaw (SMG)",                 "tags": ["act1", "the-pickup"]},
      {"id": "_weapon_plan_b",           "name": "Plan B (Pistol)",               "tags": ["act2", "playing-for-time"]},
      {"id": "_weapon_cocktail_stick",   "name": "Cocktail Stick (Knife)",        "tags": ["act2", "automatic-love"]},
      {"id": "_weapon_sir_john",         "name": "Sir John Phallustiff (Melee)",  "tags": ["act2", "venus-in-furs"]},
      {"id": "_weapon_stinger",          "name": "Stinger (Knife)",               "tags": ["act2", "space-in-between"]},
      {"id": "_weapon_fenrir",           "name": "Fenrir (SMG)",                  "tags": ["act2", "disasterpiece"]},
      {"id": "_weapon_guillotine",       "name": "Guillotine (SMG)",              "tags": ["act2", "ex-factor"]},
      {"id": "_weapon_scalpel",          "name": "Scalpel (Katana)",              "tags": ["act2", "lightning-breaks"]},
      {"id": "_weapon_widow_maker",      "name": "Widow Maker (Tech Rifle)",      "tags": ["act2", "ghost-town", "choice"]},
      {"id": "_weapon_problem_solver",   "name": "Problem Solver (SMG)",          "tags": ["act2", "ghost-town"]},
      {"id": "_weapon_byakko",           "name": "Byakko (Katana)",               "tags": ["act2", "panam"]},
      {"id": "_weapon_ofive",            "name": "O'Five (Sniper Rifle)",         "tags": ["act2", "panam"]},
      {"id": "_weapon_psalm",            "name": "Psalm 11:6 (Assault Rifle)",    "tags": ["act2", "riders-on-storm"]},
      {"id": "_weapon_overwatch",        "name": "Overwatch (Sniper Rifle)",      "tags": ["act2", "panam"]},
      {"id": "_weapon_ba_xing_chong",    "name": "Ba Xing Chong (Shotgun)",       "tags": ["act2", "panam"]},
      {"id": "_weapon_amnesty",          "name": "Amnesty (Revolver)",            "tags": ["act2", "panam"]},
      {"id": "_weapon_crash",            "name": "Crash (Revolver)",              "tags": ["side-job", "beat-on-brat"]},
      {"id": "_weapon_bloody_maria",     "name": "Bloody Maria (Shotgun)",        "tags": ["side-job", "beat-on-brat"]},
      {"id": "_weapon_archangel",        "name": "Archangel (Revolver)",          "tags": ["side-job", "river"]},
      {"id": "_weapon_breakthrough",     "name": "Breakthrough (Sniper Rifle)",   "tags": ["side-job", "ncpd"]},
      {"id": "_weapon_mox",              "name": "Mox (Shotgun)",                 "tags": ["side-job", "judy", "choice"]},
      {"id": "_weapon_pride",            "name": "Pride (Pistol)",                "tags": ["side-job", "judy"]},
      {"id": "_weapon_erebus",           "name": "Erebus (SMG)",                  "tags": ["phantom-liberty"]},
      {"id": "_weapon_hawk",             "name": "Hawk (Assault Rifle)",          "tags": ["phantom-liberty"]},
      {"id": "_weapon_rasetsu",          "name": "Rasetsu (Sniper Rifle)",        "tags": ["phantom-liberty"]},
    ],
  },
]

# ── WEAPON GATE DATA ───────────────────────────────────────────────────────────
# Used to compute status for _weapon_* pseudo-IDs above

WEAPON_GATES = {
  "_weapon_dying_night":      {"mission": "",                  "extra_facts": []},
  "_weapon_guts":             {"mission": "",                  "extra_facts": []},
  "_weapon_blue_fang":        {"mission": "",                  "extra_facts": []},
  "_weapon_headhunter":       {"mission": "",                  "extra_facts": []},
  "_weapon_skippy":           {"mission": "",                  "extra_facts": []},
  "_weapon_comrades_hammer":  {"mission": "",                  "extra_facts": []},
  "_weapon_kongou":           {"mission": "The Heist",         "extra_facts": []},
  "_weapon_satori":           {"mission": "The Heist",         "extra_facts": []},
  "_weapon_chaos":            {"mission": "The Pickup",        "extra_facts": ["q003_royce_dead"]},
  "_weapon_buzzsaw":          {"mission": "The Pickup",        "extra_facts": []},
  "_weapon_plan_b":           {"mission": "Playing for Time",  "extra_facts": []},
  "_weapon_cocktail_stick":   {"mission": "Automatic Love",    "extra_facts": []},
  "_weapon_sir_john":         {"mission": "Venus in Furs",     "extra_facts": []},
  "_weapon_stinger":          {"mission": "The Space In Between", "extra_facts": []},
  "_weapon_fenrir":           {"mission": "Disasterpiece",     "extra_facts": []},
  "_weapon_guillotine":       {"mission": "Ex-Factor",         "extra_facts": []},
  "_weapon_scalpel":          {"mission": "Lightning Breaks",  "extra_facts": []},
  "_weapon_widow_maker":      {"mission": "Ghost Town",        "extra_facts": ["q103_helped_panam"]},
  "_weapon_problem_solver":   {"mission": "Ghost Town",        "extra_facts": []},
  "_weapon_byakko":           {"mission": "We Gotta Live Together", "extra_facts": []},
  "_weapon_ofive":            {"mission": "Both Sides, Now",   "extra_facts": []},
  "_weapon_psalm":            {"mission": "Riders on the Storm", "extra_facts": []},
  "_weapon_overwatch":        {"mission": "Riders on the Storm", "extra_facts": []},
  "_weapon_ba_xing_chong":    {"mission": "I'll Fly Away",     "extra_facts": []},
  "_weapon_amnesty":          {"mission": "Queen of the Highway", "extra_facts": []},
  "_weapon_crash":            {"mission": "Beat on the Brat",  "extra_facts": []},
  "_weapon_bloody_maria":     {"mission": "Beat on the Brat",  "extra_facts": []},
  "_weapon_archangel":        {"mission": "Following the River", "extra_facts": []},
  "_weapon_breakthrough":     {"mission": "I Fought The Law",  "extra_facts": []},
  "_weapon_mox":              {"mission": "Pisces",            "extra_facts": ["sq030_judy_lover"]},
  "_weapon_pride":            {"mission": "Pyramid Song",      "extra_facts": []},
  "_weapon_erebus":           {"mission": "Somewhat Damaged",  "extra_facts": []},
  "_weapon_hawk":             {"mission": "Somewhat Damaged",  "extra_facts": []},
  "_weapon_rasetsu":          {"mission": "Somewhat Damaged",  "extra_facts": []},
}

MISSION_TO_IDS: dict[str, list[str]] = {
  "The Rescue":                         ["mq001"],
  "The Ripperdoc":                      ["mq002"],
  "The Corpo-Rat":                      ["mq003"],
  "The Street Kid":                     ["mq008"],
  "The Nomad":                          ["mq005"],
  "Practice Makes Perfect":             ["mq010"],
  "The Pickup":                         ["q003"],
  "The Information":                    ["q004"],
  "The Heist":                          ["mq301"],
  "Playing for Time":                   ["mq011"],
  "Automatic Love":                     ["mq012"],
  "The Space In Between":               ["mq013"],
  "Disasterpiece":                      ["mq014"],
  "Ex-Factor":                          ["mq015"],
  "Venus in Furs":                      ["mq012"],
  "Ghost Town":                         ["mq021"],
  "Life During Wartime":                ["mq023"],
  "Lightning Breaks":                   ["mq022"],
  "We Gotta Live Together":             ["mq032"],
  "Both Sides, Now":                    ["mq035"],
  "Riders on the Storm":                ["mq038"],
  "I'll Fly Away":                      ["mq025"],
  "Queen of the Highway":               ["mq041"],
  "Beat on the Brat":                   ["sq004"],
  "Following the River":                ["sq012"],
  "I Fought The Law":                   ["sq018"],
  "Pisces":                             ["sq030"],
  "Pyramid Song":                       ["sq024"],
  "Somewhat Damaged":                   ["sa_ep1_32"],
}

# ── SAVE PARSING ───────────────────────────────────────────────────────────────

def fmt_time(seconds: float) -> str:
  td = timedelta(seconds=int(seconds))
  h  = td.days * 24 + td.seconds // 3600
  m  = (td.seconds % 3600) // 60
  return f"{h}h {m:02d}m"


# ── FACTSDB PARSING (sav.dat via CyberpunkPythonHacks) ─────────────────────────

def _fnv1a32(s: str) -> int:
  """FNV-1a 32-bit hash used by CP2077 for fact names."""
  h = 0x811C9DC5
  for c in s.encode():
    h = ((h ^ c) * 0x01000193) & 0xFFFFFFFF
  return h


def _read_cp_packedint(data: bytes, off: int) -> tuple[int, int]:
  """Read CP2077 custom packed int (NOT standard LEB128). Returns (value, new_off)."""
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


def _wanted_fact_hashes() -> dict[int, str]:
  """FNV1a32 hash → fact name for every fact we could need from FactsDB."""
  names: set[str] = set()
  for cat in QUEST_CATALOG:
    for q in cat["quests"]:
      qid = q["id"]
      cid = q.get("check_id", qid)
      if q.get("check_fact"):
        names.add(q["check_fact"])
      if not qid.startswith("_weapon_"):
        for n in (qid, cid,
                  f"{qid}_done", f"{cid}_done",
                  f"{qid}_finished", f"{cid}_finished",
                  f"{qid}_active", f"{cid}_active"):
          names.add(n)
  # facts used for choices / display
  names.update([
    "sq030_judy_lover", "sq012_fact_warn_river", "q003_royce_dead",
    "q103_helped_panam", "q110_voodoo_queen_dead", "q003_meredith_won",
    "ep1_side_content",
  ])
  return {_fnv1a32(n): n for n in names}


def _parse_facts_db(sav_path: Path) -> dict[str, int] | None:
  """
  Parse FactsDB from sav.dat using CyberpunkPythonHacks.
  Returns {fact_name: int_value} for all recognized fact names, or None if
  CyberpunkPythonHacks is not available or the parse fails.

  Binary layout per FactsTable node (after 4-byte node-index prefix):
    [cp_packedint]   count N
    [uint32 × N]     fact name hashes  (FNV1a32, sorted ascending)
    [uint32 × N]     fact values       (parallel array)
  """
  hack_dir = Path(__file__).parent / "tools" / "CyberpunkPythonHacks"
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

  wanted = _wanted_fact_hashes()
  result: dict[str, int] = {}

  for node in sf.nodes_info:
    try:
      if node.name.decode("ascii") != "FactsTable":
        continue
    except Exception:
      continue
    data = bytes(sf.data[node.offset : node.offset + node.size])
    off  = 4  # skip 4-byte node-index prefix added by CyberpunkPythonHacks
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


def _save_timestamp(path: Path) -> datetime:
  """Return parsed save datetime for sorting. Returns datetime.min on failure."""
  try:
    raw = json.loads(path.read_text(encoding="utf-8"))
    ts = raw["Data"]["metadata"].get("timestampString", "")
    return datetime.strptime(ts, "%H:%M:%S, %d.%m.%Y")
  except Exception:
    return datetime.min


_TS_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _build_completion_timestamps() -> dict[str, str]:
  """
  Scan all save metadata files in chronological order.
  Returns {quest_id_or_fact: "DD Mon · HH:MM"} for the earliest save where
  each ID first appeared in finishedQuests (or check_fact in the facts array).
  """
  candidates = list(SAVE_ROOT.glob("*/metadata.*.json"))
  if not candidates:
    return {}

  # Collect check_fact names we track so we can scan for them in facts arrays
  check_facts: set[str] = set()
  for cat in QUEST_CATALOG:
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


def load_latest_save(save_name: str | None) -> dict:
  pattern    = f"{save_name}/metadata.*.json" if save_name else "*/metadata.*.json"
  candidates = list(SAVE_ROOT.glob(pattern))
  if not candidates:
    sys.exit(f"[ERR] No metadata JSON found under {SAVE_ROOT}")
  latest = max(candidates, key=_save_timestamp)
  print(f"[i] Reading save: {latest}")
  raw = json.loads(latest.read_text(encoding="utf-8"))
  raw["_sav_path"] = str(latest.parent / "sav.dat")
  return raw


def parse_save(raw: dict) -> dict:
  m = raw["Data"]["metadata"]

  # ── Primary: parse FactsDB from sav.dat ───────────────────────────────────
  sav_path   = Path(raw.get("_sav_path", ""))
  sav_facts  = _parse_facts_db(sav_path) if sav_path.exists() else None

  finished:     set[str] = set()
  active_facts: set[str] = set()

  if sav_facts:
    # Derive finished set from _done / _finished facts
    for name, val in sav_facts.items():
      if val:
        active_facts.add(name)
        if name.endswith("_done"):
          finished.add(name[:-5])
        elif name.endswith("_finished"):
          finished.add(name[:-9])
    # Supplement with metadata finishedQuests for IDs that lack FactsDB facts
    # (some NCPD crimes and PL milestones only appear there)
    meta_finished = set(m.get("finishedQuests", "").split())
    extra = meta_finished - finished
    if extra:
      finished.update(extra)
      print(f"[i] FactsDB: {len(sav_facts)} facts resolved; +{len(extra)} IDs from finishedQuests fallback")
    else:
      print(f"[i] FactsDB: {len(sav_facts)} facts resolved")
  else:
    # Fallback: metadata.json only
    finished = set(m.get("finishedQuests", "").split())
    for entry in m.get("facts", []):
      key, _, val = entry.partition("=")
      if val.strip() == "1":
        active_facts.add(key.strip())

  return {
    "name":        m.get("name", "?"),
    "level":       int(m.get("level", 0)),
    "street_cred": int(m.get("streetCred", 0)),
    "life_path":   m.get("lifePath", "?"),
    "play_time":   fmt_time(m.get("playthroughTime", m.get("playTime", 0))),
    "difficulty":  m.get("difficulty", "?"),
    "build_patch": m.get("buildPatch", "?"),
    "timestamp":   m.get("timestampString", "?"),
    "is_modded":   m.get("isModded", False),
    "has_ep1":     "EP1" in m.get("additionalContentIds", []),
    "attributes": {
      "Body":  int(m.get("strength", 0)),
      "Intel": int(m.get("intelligence", 0)),
      "Reflex":int(m.get("reflexes", 0)),
      "Tech":  int(m.get("technicalAbility", 0)),
      "Cool":  int(m.get("cool", 0)),
    },
    "finished_quests": sorted(finished),
    "active_facts":    sorted(active_facts),
    "completed_at":    _build_completion_timestamps(),
    "choices": {
      "Romanced Judy":    "sq030_judy_lover"       in active_facts,
      "River — saved":    "sq012_fact_warn_river"  in active_facts,
      "Royce killed":     "q003_royce_dead"        in active_facts,
      "Helped Panam":     "q103_helped_panam"      in active_facts,
      "Voodoo Queen dead":"q110_voodoo_queen_dead" in active_facts,
      "Meredith won":     "q003_meredith_won"      in active_facts,
      "PL active":        "ep1_side_content"       in active_facts,
    },
  }

# ── COMPLETION LOGIC ───────────────────────────────────────────────────────────

def _load_tracker_weapons() -> dict[str, bool]:
  """Load tracker_weapons.json if it exists (written by read_inventory.py)."""
  p = Path(__file__).parent / "tracker_weapons.json"
  if p.exists():
    try:
      return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
      pass
  return {}

_TRACKER_WEAPONS: dict[str, bool] = _load_tracker_weapons()


def quest_done(quest_id: str, finished: set[str], facts: set[str],
               check_fact: str | None = None) -> bool:
  if quest_id.startswith("_weapon_"):
    return _TRACKER_WEAPONS.get(quest_id, False)
  if check_fact:
    return check_fact in facts
  return quest_id in finished


_LIFE_PATH_TAG = {
  "Corporate": "corpo",
  "Nomad":     "nomad",
  "StreetKid": "street-kid",
}
_ALL_LIFE_PATH_TAGS = set(_LIFE_PATH_TAG.values())

def build_catalog_data(save: dict) -> list[dict]:
  finished     = set(save["finished_quests"])
  facts        = set(save["active_facts"])
  completed_at = save.get("completed_at", {})
  player_lp    = _LIFE_PATH_TAG.get(save.get("life_path", ""), "")
  catalogued_ids: set[str] = set()
  result = []

  for cat_idx, cat in enumerate(QUEST_CATALOG):
    quests_out = []
    for q_idx, q in enumerate(cat["quests"]):
      # Skip life path quests that don't belong to this player's life path
      q_tags = set(q.get("tags", []))
      lp_tags_on_quest = q_tags & _ALL_LIFE_PATH_TAGS
      if lp_tags_on_quest and player_lp not in lp_tags_on_quest:
        continue
      check_id   = q.get("check_id", q["id"])
      check_fact = q.get("check_fact")
      done = quest_done(check_id, finished, facts, check_fact)
      catalogued_ids.add(check_id)
      ts_key = check_fact if check_fact else check_id
      quests_out.append({
        "id":           q["id"],
        "name":         q["name"],
        "dep":          q.get("dep", ""),
        "wiki":         q.get("wiki"),  # None=auto, False=suppress, str=custom slug
        "tags":         q.get("tags", []) + cat.get("tags", []),
        "done":         done,
        "seq":          q_idx,
        "cat_seq":      cat_idx * 1000,
        "manual":       q["id"].startswith("_weapon_"),
        "completed_at": completed_at.get(ts_key, ""),
      })
    total     = len(quests_out)
    completed = sum(1 for q in quests_out if q["done"])
    result.append({
      "id":        cat["id"],
      "label":     cat["label"],
      "color":     cat["color"],
      "icon":      cat["icon"],
      "note":      cat.get("note", ""),
      "show_wiki": cat.get("show_wiki", True),
      "completed": completed,
      "total":     total,
      "pct":       round(100 * completed / total) if total else 0,
      "quests":    quests_out,
    })

  # Parent-group completion flags (auto-complete when all sub-quests finish; already tracked indirectly)
  PARENT_FLAGS = {"q000", "q001"}
  # Dogtown airdrop sandbox activities — unnamed loot-crate events, not trackable quests
  AIRDROP_IDS  = {"sa_ep1_31","sa_ep1_32","sa_ep1_34","sa_ep1_37","sa_ep1_38","sa_ep1_39","sa_ep1_303"}
  SUPPRESS     = PARENT_FLAGS | AIRDROP_IDS
  # Uncatalogued quests from save
  extra = sorted(q for q in finished if q not in catalogued_ids and not q.startswith("_") and q not in SUPPRESS)
  if extra:
    result.append({
      "id": "uncatalogued", "label": "Uncatalogued", "color": "#555",
      "icon": "?", "completed": len(extra), "total": len(extra), "pct": 100,
      "quests": [{"id": q, "name": q, "tags": ["uncatalogued"], "done": True} for q in extra],
    })

  return result


# ── HTML TEMPLATE ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CP2077 · 100% Tracker</title>
<style>
:root {
  --bg:#080810; --panel:#0e0e1a; --border:#1a1a2c; --text:#dde; --muted:#667;
  --cyan:#00d4ff; --yellow:#f0e040; --green:#39d353; --red:#ff4455;
  --orange:#ff8833; --purple:#cc66ff;
  font-size:13px;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Courier New',monospace}

/* scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:var(--panel)}
::-webkit-scrollbar-thumb{background:var(--border)}

/* ── header ── */
header{padding:18px 24px 12px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-wrap:wrap}
header h1{font-size:18px;letter-spacing:4px;color:var(--cyan);text-transform:uppercase;flex:1}
header h1 span{color:var(--yellow)}
.save-badge{font-size:11px;color:var(--muted);letter-spacing:1px}
.save-badge b{color:var(--text)}

/* ── layout ── */
.layout{display:grid;grid-template-columns:240px 1fr;min-height:calc(100vh - 56px)}

/* ── sidebar ── */
aside{background:var(--panel);border-right:1px solid var(--border);padding:12px;overflow-y:auto;max-height:calc(100vh - 56px);position:sticky;top:0}
.s-title{font-size:9px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin:14px 0 6px;border-bottom:1px solid var(--border);padding-bottom:3px}
.s-title:first-child{margin-top:0}
.s-row{display:flex;justify-content:space-between;padding:2px 0;font-size:12px}
.s-label{color:var(--muted)}
.s-val{font-weight:bold}
.c-yes{color:var(--green)}.c-no{color:var(--muted)}.c-cyan{color:var(--cyan)}.c-yellow{color:var(--yellow)}
.attr-grid{display:grid;grid-template-columns:1fr 1fr;gap:2px 8px}

/* ── main ── */
main{padding:16px 20px;overflow-y:auto;max-height:calc(100vh - 56px)}

/* ── overall progress ── */
.overall{background:var(--panel);border:1px solid var(--border);padding:14px 16px;margin-bottom:16px;border-radius:2px}
.overall-title{font-size:10px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin-bottom:10px}
.overall-bar-wrap{background:#111;height:10px;border-radius:1px;overflow:hidden;margin-bottom:6px}
.overall-bar{height:100%;background:linear-gradient(90deg,var(--cyan),var(--green));transition:width .4s}
.overall-summary{font-size:11px;color:var(--muted)}
.overall-summary b{color:var(--text)}

/* ── sidebar progress ── */
.s-prog-item{margin-bottom:5px}
.s-prog-row{display:flex;justify-content:space-between;padding:1px 0;font-size:11px;cursor:pointer;border-radius:1px;transition:opacity .1s}
.s-prog-row:hover{opacity:.8}
.s-prog-label{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:155px}
.s-prog-val{font-weight:bold;flex-shrink:0;margin-left:4px}

/* ── toolbar ── */
.toolbar{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;align-items:center}
input[type=search]{background:var(--panel);border:1px solid var(--border);color:var(--text);padding:5px 10px;font-family:inherit;font-size:12px;width:220px;outline:none}
input[type=search]:focus{border-color:var(--cyan)}
input[type=search]::placeholder{color:var(--muted)}
.filter-btn,.sort-btn{padding:4px 10px;background:var(--panel);border:1px solid var(--border);color:var(--muted);cursor:pointer;font-family:inherit;font-size:10px;letter-spacing:1px;text-transform:uppercase;transition:all .15s}
.filter-btn:hover,.filter-btn.active{border-color:var(--cyan);color:var(--cyan);background:#001a22}
.sort-btn:hover,.sort-btn.active{border-color:var(--yellow);color:var(--yellow);background:#1a1500}
.toolbar-sep{width:1px;background:var(--border);align-self:stretch;margin:0 4px}
.toolbar-label{font-size:9px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;align-self:center;white-space:nowrap}
.count-badge{background:#111;border:1px solid var(--border);padding:4px 10px;font-size:10px;color:var(--muted);letter-spacing:1px;margin-left:auto}
.count-badge b{color:var(--text)}

/* ── category cards grid ── */
.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:8px;margin-bottom:16px}
.cat-card{background:var(--panel);border:1px solid var(--border);padding:10px 12px;cursor:pointer;transition:border-color .15s;border-radius:2px}
.cat-card:hover,.cat-card.active{border-color:var(--cyan)}
.cat-card.active{background:#001a22}
.cat-card-head{display:flex;align-items:center;gap:6px;margin-bottom:6px}
.cat-icon{font-size:14px}
.cat-label{font-size:11px;letter-spacing:1px;text-transform:uppercase;font-weight:bold;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat-counts{font-size:10px;color:var(--muted);letter-spacing:1px}
.cat-counts b{color:var(--text)}
.mini-bar{height:3px;background:#1a1a2a;border-radius:1px;overflow:hidden;margin-top:4px}
.mini-fill{height:100%;border-radius:1px}

/* ── quest list ── */
.quest-panel{background:var(--panel);border:1px solid var(--border);border-radius:2px;margin-bottom:16px}
.quest-panel-head{padding:10px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border)}
.quest-panel-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:bold}
.quest-panel-sub{font-size:10px;color:var(--muted);margin-left:auto;letter-spacing:1px}

.quest-row{display:flex;align-items:flex-start;gap:10px;padding:6px 14px;border-bottom:1px solid #0a0a16;transition:background .1s}
.quest-row:last-child{border-bottom:none}
.quest-row:hover{background:#0c0c1a}
.quest-row.hidden{display:none}
.q-check{font-size:14px;line-height:1;margin-top:1px;flex-shrink:0}
.q-done .q-check{color:var(--green)}
.q-todo .q-check{color:#333}
.q-info{flex:1;min-width:0}
.q-name{font-size:12px;color:var(--text);line-height:1.3}
.q-todo .q-name{color:var(--muted)}
.q-dep{font-size:9px;color:#3a6a8a;letter-spacing:.3px;margin-left:6px;opacity:.8}
.q-id{font-size:10px;color:#445;margin-top:1px;font-family:'Courier New',monospace}
.q-ts{font-size:9px;color:#2a5a3a;margin-left:8px;letter-spacing:.3px;opacity:.8}
.q-tags{display:flex;flex-wrap:wrap;gap:3px;margin-top:4px}
.q-tag{font-size:9px;padding:1px 5px;border-radius:1px;border:1px solid;cursor:pointer;letter-spacing:.5px;white-space:nowrap}
.q-tag:hover{opacity:.8}

/* district tag colours */
.t-watson{background:#0a1a2a;border-color:#1a3a5a;color:#6699cc}
.t-westbrook{background:#1a0a2a;border-color:#3a1a5a;color:#9966cc}
.t-city-center{background:#2a1a0a;border-color:#5a3a1a;color:#cc9944}
.t-heywood{background:#0a2a0a;border-color:#1a5a1a;color:#66cc66}
.t-santo-domingo{background:#2a0a0a;border-color:#5a1a1a;color:#cc6644}
.t-badlands{background:#1a1a0a;border-color:#3a3a1a;color:#aaaa44}
.t-pacifica{background:#0a2a2a;border-color:#1a4a4a;color:#44aaaa}
.t-dogtown{background:#2a0a2a;border-color:#5a1a5a;color:#cc44cc}
/* content type colours */
.t-main-story,.t-act1,.t-act2,.t-act3,.t-prologue,.t-ending{background:#001a22;border-color:#003344;color:#00aacc}
.t-side-job{background:#1a1a00;border-color:#3a3a00;color:#aaaa00}
.t-gig{background:#001a00;border-color:#003300;color:#00aa00}
.t-cyberpsycho,.t-ncpd{background:#1a0000;border-color:#330000;color:#aa4444}
.t-phantom-liberty,.t-dlc,.t-pl-main,.t-pl-side{background:#1a001a;border-color:#330033;color:#aa44aa}
.t-weapon,.t-iconic{background:#1a1600;border-color:#332c00;color:#998800}
.t-choice{background:#001a0a;border-color:#003a1a;color:#00aa55}
.t-judy,.t-panam,.t-river,.t-kerry,.t-johnny,.t-rogue{background:#0a0a1a;border-color:#1a1a3a;color:#7777cc}
.t-open-world{background:#0a1a0a;border-color:#1a3a1a;color:#44aa44}
.t-bounty{background:#1a0a00;border-color:#3a1a00;color:#aa6600}

/* generic fallback */
.q-tag{background:#111;border-color:#333;color:#666}

.hidden{display:none!important}

/* ── manual (weapon) rows ── */
.quest-row[data-manual="true"]{cursor:pointer}
.quest-row[data-manual="true"]:hover .q-check{color:var(--yellow)}
.q-panel-note{font-size:9px;color:var(--muted);letter-spacing:.5px;padding:4px 14px 6px;font-style:italic;border-bottom:1px solid var(--border)}

/* ── wiki link ── */
.q-wiki{display:inline-flex;align-items:center;gap:3px;font-size:9px;font-family:inherit;letter-spacing:.5px;text-transform:uppercase;font-weight:700;color:#6cf;text-decoration:none;margin-left:8px;padding:1px 6px;border:1px solid #2a4a6a;border-radius:3px;background:#0a1a2a;opacity:.65;vertical-align:middle;transition:opacity .15s,background .15s,border-color .15s}
.q-wiki:hover{opacity:1;background:#0d2840;border-color:#4a9aca;color:#9de}

/* ── report button ── */
.q-report{display:none;margin-left:6px;padding:1px 5px;font-size:9px;font-family:inherit;letter-spacing:.5px;text-transform:uppercase;font-weight:700;color:#a44;border:1px solid #4a1a1a;border-radius:3px;background:#1a0808;cursor:pointer;vertical-align:middle;opacity:.7;transition:opacity .15s}
.quest-row:hover .q-report{display:inline-flex}
.q-report:hover{opacity:1;background:#2a0c0c;border-color:#8a2a2a;color:#f66}

/* ── report modal ── */
#reportModal{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;align-items:center;justify-content:center}
#reportModal.open{display:flex}
.report-box{background:#0d0d1a;border:1px solid #2a2a4a;border-radius:8px;padding:24px;width:480px;max-width:90vw;font-family:inherit}
.report-box h3{margin:0 0 14px;font-size:13px;letter-spacing:1px;color:var(--yellow)}
.report-box label{font-size:10px;color:var(--muted);letter-spacing:.5px;display:block;margin-bottom:4px}
.report-box textarea{width:100%;box-sizing:border-box;background:#06060f;border:1px solid #2a2a4a;color:var(--text);font-family:inherit;font-size:11px;padding:8px;border-radius:4px;resize:vertical;min-height:70px;outline:none}
.report-box textarea:focus{border-color:#4a4a8a}
.report-meta{font-size:10px;color:#556;margin-bottom:12px;line-height:1.7;background:#06060f;border:1px solid #1a1a2a;border-radius:4px;padding:8px}
.report-actions{display:flex;gap:8px;justify-content:flex-end;margin-top:14px}
.report-actions button{font-family:inherit;font-size:10px;letter-spacing:.5px;text-transform:uppercase;padding:5px 14px;border-radius:4px;cursor:pointer;font-weight:700}
.btn-copy{background:#0a2a0a;border:1px solid #2a5a2a;color:#6f6;transition:background .15s}
.btn-copy:hover{background:#0d3a0d}
.btn-cancel{background:#1a0a0a;border:1px solid #3a1a1a;color:#a66;transition:background .15s}
.btn-cancel:hover{background:#2a0d0d}
.copy-confirm{font-size:10px;color:#6f6;opacity:0;transition:opacity .3s;align-self:center}

/* ── report queue button in header ── */
.report-queue-btn{font-family:inherit;font-size:10px;letter-spacing:.5px;text-transform:uppercase;font-weight:700;color:#fa3;background:#1a0f00;border:1px solid #4a3a00;border-radius:4px;padding:4px 10px;cursor:pointer;margin-left:auto;transition:background .15s}
.report-queue-btn:hover{background:#2a1a00;border-color:#8a6a00}
.report-badge{display:inline-block;background:#e63;color:#fff;font-size:9px;padding:0 5px;border-radius:8px;margin-left:4px;font-weight:700;vertical-align:middle}

/* ── queue panel ── */
#queuePanel{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;align-items:center;justify-content:center}
#queuePanel.open{display:flex}
.queue-box{width:560px;max-width:92vw;max-height:80vh;display:flex;flex-direction:column}
#queueList{overflow-y:auto;flex:1;display:flex;flex-direction:column;gap:8px;min-height:40px;max-height:380px;padding-right:4px}
.queue-item{background:#06060f;border:1px solid #1a1a2a;border-radius:4px;padding:10px 12px}
.queue-item-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.queue-item-name{font-size:12px;font-weight:700;color:var(--yellow)}
.queue-remove{background:none;border:none;color:#833;cursor:pointer;font-size:13px;padding:0 2px;line-height:1}
.queue-remove:hover{color:#f66}
.queue-item-meta{font-size:10px;color:var(--muted);margin-bottom:4px}
.queue-item-issue{font-size:11px;color:var(--text)}
</style>
</head>
<body>
<header>
  <h1>CYBERPUNK <span>2077</span> · 100% TRACKER</h1>
  <div class="save-badge" id="saveBadge"></div>
  <button class="report-queue-btn" id="reportQueueBtn" onclick="openQueue()" style="display:none" title="View queued reports">
    ⚑ Reports <span class="report-badge" id="reportBadge"></span>
  </button>
</header>

<div class="layout">
  <aside id="sidebar"></aside>
  <main>
    <div class="overall" id="overallBox"></div>
    <div class="toolbar">
      <span class="toolbar-label">Filter:</span>
      <button class="filter-btn active" data-f="all">All</button>
      <button class="filter-btn" data-f="todo">Incomplete</button>
      <button class="filter-btn" data-f="done">Completed</button>
      <div class="toolbar-sep"></div>
      <span class="toolbar-label">Sort:</span>
      <button class="sort-btn active" data-s="seq">Unlock Order</button>
      <button class="sort-btn" data-s="az">A → Z</button>
      <button class="sort-btn" data-s="todo_first">Incomplete First</button>
      <button class="sort-btn" data-s="done_first">Completed First</button>
      <input type="search" id="searchBox" placeholder="Search quests, IDs, tags…">
      <span class="count-badge" id="countBadge"></span>
    </div>
    <div class="cards-grid" id="cardsGrid"></div>
    <div id="questPanels"></div>
  </main>
</div>

<script>
const DATA = __DATA__;

// ── Sidebar ──────────────────────────────────────────────────────────────────
function renderSidebar() {
  const s = DATA.save;
  const r = (l,v,c='')=>`<div class="s-row"><span class="s-label">${l}</span><span class="s-val ${c}">${v}</span></div>`;
  document.getElementById('sidebar').innerHTML = `
    <div class="s-title">Player</div>
    ${r('Level',       s.level,       'c-cyan')}
    ${r('Street Cred', s.street_cred, 'c-cyan')}
    ${r('Life Path',   s.life_path)}
    ${r('Difficulty',  s.difficulty)}
    ${r('Play Time',   s.play_time,   'c-yellow')}
    ${r('Patch',       s.build_patch)}
    ${r('PL',          s.has_ep1?'Yes':'No', s.has_ep1?'c-yes':'c-no')}
    ${r('Modded',      s.is_modded?'Yes':'No', s.is_modded?'c-yellow':'')}
    <div class="s-title">Attributes</div>
    <div class="attr-grid">${Object.entries(s.attributes).map(([k,v])=>
      `<div class="s-row"><span class="s-label">${k}</span><span class="s-val c-cyan">${v}</span></div>`).join('')}
    </div>
    <div class="s-title">Choices</div>
    ${Object.entries(s.choices).map(([k,v])=>
      `<div class="s-row"><span class="s-label">${k}</span><span class="${v?'c-yes':'c-no'}">${v?'Yes':'No'}</span></div>`).join('')}
    <div class="s-title">Progress</div>
    <div id="sidebarProgress"></div>
  `;
  document.getElementById('saveBadge').innerHTML =
    `Save: <b>${s.name}</b> &nbsp;|&nbsp; ${s.timestamp}`;
}

function renderSidebarProgress() {
  const el = document.getElementById('sidebarProgress');
  if (!el) return;
  const cats = DATA.catalog.filter(c => c.id !== 'uncatalogued');
  el.innerHTML = cats.map(c => `
    <div class="s-prog-item">
      <div class="s-prog-row" data-cat="${c.id}" onclick="navigateToCategory('${c.id}')">
        <span class="s-prog-label" style="color:${c.color}">${c.icon} ${c.label}</span>
        <span class="s-prog-val" style="color:${c.color}">${c.completed}/${c.total}</span>
      </div>
      <div class="mini-bar"><div class="mini-fill" style="width:${c.pct}%;background:${c.color}"></div></div>
    </div>`).join('');
}

// ── Overall progress ─────────────────────────────────────────────────────────
function renderOverall() {
  const cats = DATA.catalog.filter(c=>c.id!=='uncatalogued');
  const totalQ = cats.reduce((a,c)=>a+c.total,0);
  const doneQ  = cats.reduce((a,c)=>a+c.completed,0);
  const pct    = totalQ ? Math.round(100*doneQ/totalQ) : 0;
  document.getElementById('overallBox').innerHTML = `
    <div class="overall-title">Overall Completion</div>
    <div class="overall-bar-wrap"><div class="overall-bar" style="width:${pct}%"></div></div>
    <div class="overall-summary"><b>${pct}%</b> complete &nbsp;·&nbsp; <b>${doneQ}</b> / <b>${totalQ}</b> tracked activities</div>`;
  renderSidebarProgress();
}

// ── Category navigation ───────────────────────────────────────────────────────
let activeCategory = 'all';

function setCategory(catId) {
  activeCategory = catId;
  renderCards();
  renderQuestPanels();
}

function navigateToCategory(catId) {
  const hash = catId === 'all' ? '' : catId;
  history.pushState(null, '', hash ? '#' + hash : window.location.pathname + window.location.search);
  setCategory(catId);
}

window.addEventListener('popstate', () => {
  const catId = location.hash.slice(1) || 'all';
  const exists = catId === 'all' || DATA.catalog.some(c => c.id === catId);
  if (exists) setCategory(catId);
});

// ── Category cards ────────────────────────────────────────────────────────────
function renderCards() {
  const grid = document.getElementById('cardsGrid');
  // "All" card
  const total = DATA.catalog.reduce((a,c)=>a+c.total,0);
  const done  = DATA.catalog.reduce((a,c)=>a+c.completed,0);
  grid.innerHTML = `
    <div class="cat-card${activeCategory==='all'?' active':''}" data-cat="all">
      <div class="cat-card-head">
        <span class="cat-icon" style="color:var(--cyan)">◈</span>
        <span class="cat-label" style="color:var(--cyan)">All Categories</span>
      </div>
      <div class="cat-counts"><b>${done}</b> / ${total}</div>
      <div class="mini-bar"><div class="mini-fill" style="width:${Math.round(100*done/total)}%;background:var(--cyan)"></div></div>
    </div>
    ${DATA.catalog.map(c=>`
    <div class="cat-card${activeCategory===c.id?' active':''}" data-cat="${c.id}">
      <div class="cat-card-head">
        <span class="cat-icon" style="color:${c.color}">${c.icon}</span>
        <span class="cat-label" style="color:${c.color}">${c.label}</span>
      </div>
      <div class="cat-counts"><b>${c.completed}</b> / ${c.total} &nbsp; <b>${c.pct}%</b></div>
      <div class="mini-bar"><div class="mini-fill" style="width:${c.pct}%;background:${c.color}"></div></div>
    </div>`).join('')}`;
  grid.querySelectorAll('.cat-card').forEach(card=>{
    card.addEventListener('click',()=>{
      navigateToCategory(card.dataset.cat);
    });
  });
}

// ── Sort ──────────────────────────────────────────────────────────────────────
let activeSort = 'seq';

function sortQuests(quests) {
  const arr = [...quests];
  if (activeSort === 'az') {
    arr.sort((a,b) => a.name.localeCompare(b.name));
  } else if (activeSort === 'todo_first') {
    arr.sort((a,b) => a.done !== b.done ? (a.done ? 1 : -1) : a.seq - b.seq);
  } else if (activeSort === 'done_first') {
    arr.sort((a,b) => a.done !== b.done ? (a.done ? -1 : 1) : a.seq - b.seq);
  }
  // 'seq' (default): already in catalog order
  return arr;
}

// ── Manual weapon tracking (localStorage) ────────────────────────────────────
function applyManualOverrides() {
  const stored = JSON.parse(localStorage.getItem('cp2077_weapons') || '{}');
  DATA.catalog.forEach(cat => {
    let hasManual = false;
    cat.quests.forEach(q => {
      if (q.manual) {
        // localStorage explicitly overrides Python-provided status (from read_inventory.py)
        if (q.id in stored) q.done = stored[q.id] === true;
        // else keep q.done as set by Python (tracker_weapons.json)
        hasManual = true;
      }
    });
    if (hasManual) {
      cat.completed = cat.quests.filter(q => q.done).length;
      cat.pct = cat.total ? Math.round(100 * cat.completed / cat.total) : 0;
    }
  });
}

function toggleWeapon(qid) {
  const stored = JSON.parse(localStorage.getItem('cp2077_weapons') || '{}');
  // Find current effective state (localStorage override or Python default)
  const q = DATA.catalog.flatMap(c => c.quests).find(q => q.id === qid);
  const cur = q ? q.done : (stored[qid] === true);
  stored[qid] = !cur;
  localStorage.setItem('cp2077_weapons', JSON.stringify(stored));
  applyManualOverrides();
  renderOverall();
  renderCards();
  renderQuestPanels();
}

// ── Quest panels ──────────────────────────────────────────────────────────────
function renderQuestPanels() {
  const cats = activeCategory==='all' ? DATA.catalog : DATA.catalog.filter(c=>c.id===activeCategory);
  const panels = document.getElementById('questPanels');
  panels.innerHTML = cats.map(cat=>`
    <div class="quest-panel" data-panel="${cat.id}">
      <div class="quest-panel-head" style="border-left:3px solid ${cat.color}">
        <span style="color:${cat.color}">${cat.icon}</span>
        <span class="quest-panel-title" style="color:${cat.color}">${cat.label}</span>
        <span class="quest-panel-sub">${cat.completed}/${cat.total} · ${cat.pct}%</span>
      </div>
      ${cat.note ? `<div class="q-panel-note">${cat.note}</div>` : ''}
      ${sortQuests(cat.quests).map(q=>{
        const dedup=[...new Set(q.tags)];
        let wikiUrl = null;
        if (cat.show_wiki !== false && q.wiki !== false) {
          if (q.wiki) {
            // explicit slug from Python
            wikiUrl = `https://cyberpunk.fandom.com/wiki/${encodeURIComponent(q.wiki)}`;
          } else {
            // auto-generate: take first quest before → or /, strip trailing parenthetical annotations
            const baseName = q.name.split('→')[0].split(' / ')[0].trim().replace(/\s*\([^)]*\)\s*$/, '').trim();
            if (baseName) wikiUrl = `https://cyberpunk.fandom.com/wiki/${encodeURIComponent(baseName.replace(/ /g,'_'))}`;
          }
        }
        return `<div class="quest-row ${q.done?'q-done':'q-todo'}" data-done="${q.done}" data-id="${q.id}" data-name="${q.name.toLowerCase()}" data-tags="${dedup.join(' ')}" data-manual="${q.manual||false}">
          <span class="q-check">${q.done?'✓':'○'}</span>
          <div class="q-info">
            <div class="q-name">${q.name}${q.dep?`<span class="q-dep">▸ ${q.dep}</span>`:''}${wikiUrl?` <a class="q-wiki" href="${wikiUrl}" target="_blank" title="Open on Cyberpunk wiki" onclick="event.stopPropagation()">WIKI ↗</a>`:''}<button class="q-report" onclick="reportIssue('${q.id}','${cat.label.replace(/'/g,"\\'")}','${q.name.replace(/'/g,"\\'")}',${q.done},event)" title="Report issue">⚑ REPORT</button></div>
            <div class="q-id">${q.id}${q.done&&q.completed_at?`<span class="q-ts">${q.completed_at}</span>`:''}</div>
            <div class="q-tags">${dedup.map(t=>`<span class="q-tag t-${t}" data-tag="${t}">${t}</span>`).join('')}</div>
          </div>
        </div>`;
      }).join('')}
    </div>`).join('');

  // tag click → search by tag
  panels.querySelectorAll('.q-tag').forEach(tag=>{
    tag.addEventListener('click', e=>{
      e.stopPropagation();
      document.getElementById('searchBox').value = tag.dataset.tag;
      applyFilters();
    });
  });

  // manual weapon rows → click to toggle collected
  panels.querySelectorAll('.quest-row[data-manual="true"]').forEach(row=>{
    row.addEventListener('click', e=>{
      if (e.target.closest('a,button,.q-tag')) return;
      toggleWeapon(row.dataset.id);
    });
  });

  applyFilters();
}

// ── Filters ───────────────────────────────────────────────────────────────────
let activeFilter = 'all';
function applyFilters() {
  const q   = document.getElementById('searchBox').value.toLowerCase().trim();
  const rows = document.querySelectorAll('.quest-row');
  let vis = 0;
  rows.forEach(row=>{
    const filterOk = activeFilter==='all'
      || (activeFilter==='done' && row.dataset.done==='true')
      || (activeFilter==='todo' && row.dataset.done==='false');
    const searchOk = !q
      || row.dataset.name.includes(q)
      || row.dataset.id.includes(q)
      || row.dataset.tags.includes(q);
    const show = filterOk && searchOk;
    row.classList.toggle('hidden', !show);
    if(show) vis++;
  });
  document.getElementById('countBadge').innerHTML = `<b>${vis}</b> shown`;
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  applyManualOverrides();
  // restore active category from URL hash if present
  const initHash = location.hash.slice(1);
  if (initHash && DATA.catalog.some(c => c.id === initHash)) {
    activeCategory = initHash;
  }
  renderSidebar();
  renderOverall();
  renderCards();
  renderQuestPanels();

  document.querySelectorAll('.filter-btn').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('.filter-btn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      activeFilter = b.dataset.f;
      applyFilters();
    });
  });

  document.querySelectorAll('.sort-btn').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('.sort-btn').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      activeSort = b.dataset.s;
      renderQuestPanels();
    });
  });

  document.getElementById('searchBox').addEventListener('input', applyFilters);
});

// ── Issue reporter ─────────────────────────────────────────────────────────
const QUEUE_KEY = 'cp2077_reports';

function getQueue() {
  try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]'); }
  catch { return []; }
}
function saveQueue(q) {
  localStorage.setItem(QUEUE_KEY, JSON.stringify(q));
  updateQueueBadge();
}
function updateQueueBadge() {
  const n = getQueue().length;
  const badge = document.getElementById('reportBadge');
  const btn   = document.getElementById('reportQueueBtn');
  badge.textContent = n;
  badge.style.display = n ? 'inline' : 'none';
  btn.style.display   = n ? 'inline-flex' : 'none';
}

function reportIssue(id, cat, name, done, ev) {
  ev.stopPropagation();
  const save = (DATA.save && DATA.save.name) || '?';
  const status = done ? 'shows DONE' : 'shows TODO';
  document.getElementById('rMeta').textContent =
    `Quest: ${name}\\nID: ${id}\\nCategory: ${cat}\\nStatus: ${status}\\nSave: ${save}`;
  document.getElementById('rDesc').value = '';
  document.getElementById('rAddConfirm').style.opacity = '0';
  document.getElementById('reportModal').classList.add('open');
  document.getElementById('rDesc').focus();
  document.getElementById('reportModal')._data = {id, cat, name, done, save, status};
}
function closeReport() {
  document.getElementById('reportModal').classList.remove('open');
}
function addToQueue() {
  const d    = document.getElementById('reportModal')._data;
  const desc = document.getElementById('rDesc').value.trim() || '(no description)';
  const q    = getQueue();
  // dedupe by id+desc
  if (!q.find(r => r.id === d.id && r.desc === desc)) {
    q.push({id: d.id, cat: d.cat, name: d.name, status: d.status, save: d.save, desc, ts: Date.now()});
    saveQueue(q);
  }
  const el = document.getElementById('rAddConfirm');
  el.style.opacity = '1';
  setTimeout(()=>{ el.style.opacity='0'; closeReport(); }, 900);
}

// Queue panel
function openQueue() {
  renderQueuePanel();
  document.getElementById('queuePanel').classList.add('open');
}
function closeQueue() {
  document.getElementById('queuePanel').classList.remove('open');
}
function removeFromQueue(idx) {
  const q = getQueue();
  q.splice(idx, 1);
  saveQueue(q);
  renderQueuePanel();
}
function renderQueuePanel() {
  const q = getQueue();
  document.getElementById('qCount').textContent = q.length ? `(${q.length})` : '';
  const list = document.getElementById('queueList');
  if (!q.length) {
    list.innerHTML = '<p style="color:#888;font-size:12px;margin:0">No reports queued.</p>';
    return;
  }
  list.innerHTML = q.map((r, i) => `
    <div class="queue-item">
      <div class="queue-item-header">
        <span class="queue-item-name">${r.name}</span>
        <button class="queue-remove" onclick="removeFromQueue(${i})" title="Remove">✕</button>
      </div>
      <div class="queue-item-meta">${r.id} · ${r.cat} · ${r.status}</div>
      <div class="queue-item-issue">${r.desc}</div>
    </div>`).join('');
}
function copyAllReports() {
  const q = getQueue();
  if (!q.length) return;
  const save = q[0].save;
  const lines = [
    `[CP2077 TRACKER BUG REPORTS] — ${q.length} issue${q.length>1?'s':''}`,
    `Save: ${save}`,
    '',
    ...q.map((r, i) => [
      `${i+1}. Quest: ${r.name}`,
      `   ID: ${r.id}`,
      `   Category: ${r.cat}`,
      `   Status: ${r.status}`,
      `   Issue: ${r.desc}`,
    ].join('\\n')),
  ];
  navigator.clipboard.writeText(lines.join('\\n')).then(()=>{
    const el = document.getElementById('qCopyConfirm');
    el.style.opacity = '1';
    setTimeout(()=>{ el.style.opacity='0'; saveQueue([]); renderQueuePanel(); }, 1400);
  });
}

document.addEventListener('keydown', e=>{
  if(e.key==='Escape'){
    closeReport();
    closeQueue();
  }
});
document.addEventListener('DOMContentLoaded', updateQueueBadge);
</script>

<div id="reportModal" onclick="if(event.target===this)closeReport()">
  <div class="report-box">
    <h3>REPORT TRACKER ISSUE</h3>
    <label>ENTRY</label>
    <pre class="report-meta" id="rMeta"></pre>
    <label>WHAT'S WRONG?</label>
    <textarea id="rDesc" placeholder="e.g. Shows as done but I haven't done it / wrong name / should be split into 2 entries / missing entry..."></textarea>
    <div class="report-actions">
      <span class="copy-confirm" id="rAddConfirm">Added!</span>
      <button class="btn-cancel" onclick="closeReport()">Cancel</button>
      <button class="btn-copy" onclick="addToQueue()">Add to Queue</button>
    </div>
  </div>
</div>

<div id="queuePanel" onclick="if(event.target===this)closeQueue()">
  <div class="report-box queue-box">
    <h3>QUEUED REPORTS <span id="qCount"></span></h3>
    <div id="queueList"></div>
    <div class="report-actions" style="margin-top:12px">
      <span class="copy-confirm" id="qCopyConfirm">Copied &amp; cleared!</span>
      <button class="btn-cancel" onclick="closeQueue()">Close</button>
      <button class="btn-copy" onclick="copyAllReports()">Copy All &amp; Clear</button>
    </div>
  </div>
</div>
</body>
</html>
"""

# ── HTML GENERATION ────────────────────────────────────────────────────────────

def generate_html(save: dict) -> str:
  catalog = build_catalog_data(save)
  payload = {"save": save, "catalog": catalog}
  return HTML_TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
  parser = argparse.ArgumentParser(description="CP2077 100% Completion Tracker")
  parser.add_argument("--save",    metavar="FOLDER")
  parser.add_argument("--no-open", action="store_true")
  parser.add_argument("--output",  metavar="FILE", default=str(OUTPUT_FILE))
  args = parser.parse_args()

  raw  = load_latest_save(args.save)
  save = parse_save(raw)

  catalog = build_catalog_data(save)
  total   = sum(c["total"]     for c in catalog if c["id"] != "uncatalogued")
  done    = sum(c["completed"] for c in catalog if c["id"] != "uncatalogued")
  print(f"[+] {save['name']}  Level {save['level']}  {save['play_time']}")
  print(f"[+] Overall: {done}/{total}  ({round(100*done/total)}%)")
  for c in catalog:
    bar  = "#" * (c["pct"]//5) + "." * (20 - c["pct"]//5)
    print(f"    {bar}  {c['pct']:3d}%  {c['completed']:3d}/{c['total']:<3d}  {c['label']}")

  html = generate_html(save)
  out  = Path(args.output)
  out.write_text(html, encoding="utf-8")
  print(f"[+] Written: {out}")

  if not args.no_open:
    webbrowser.open(out.as_uri())


if __name__ == "__main__":
  main()

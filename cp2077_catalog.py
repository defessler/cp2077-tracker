"""
cp2077_catalog.py — Cyberpunk 2077 quest catalog and game-specific metadata.

To update this catalog:
  - Add/remove quest entries from QUEST_CATALOG
  - Update SUPPRESS_IDS when the save writes parent/duplicate IDs that are
    already tracked under a different entry (check audit output for uncatalogued)
  - LIFE_PATH_TAG maps save 'lifePath' values to the tag strings used on quests
"""
from __future__ import annotations

# ── Quest catalog ──────────────────────────────────────────────────────────────
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
      {"id": "sq032",             "name": "Tapeworm",             "dep": "4 phases auto-trigger across Act 2", "tags": ["act2", "johnny"]},
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
      {"id": "q112_01_old_friend",       "name": "Down on the Street",         "dep": "Playing for Time",               "check_id": "q112", "reward_key": "q112_old_friend",       "tags": ["act2", "takemura"]},
      {"id": "q112_02_industrial_park",  "name": "Gimme Danger",               "dep": "after Down on the Street",       "check_id": "q112", "reward_key": "q112_industrial_park",   "tags": ["act2", "takemura"]},
      {"id": "q112_03_dashi_parade",     "name": "Play It Safe",               "dep": "after Gimme Danger (+ Life During Wartime)", "check_id": "q112", "reward_key": "q112_dashi_parade",     "tags": ["act2", "takemura"]},
      {"id": "q112_04_hideout",          "name": "Search and Destroy",         "dep": "after Play It Safe",             "check_id": "q112", "reward_key": "q112_hideout",           "tags": ["act2", "takemura"]},
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
      # Late Act 2 — Johnny side chain unlocks after Tapeworm completes
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
      {"id": "q307_tomorrow",       "name": "Things Done Changed",              "dep": "Reed path epilogue (after From Her to Eternity)",        "check_fact": "q307_done", "tags": ["pl-main", "ending", "reed"]},
      {"id": "q307_before_tomorrow","name": "Who Wants to Live Forever",        "dep": "Songbird path epilogue (after The Killing Moon)",        "check_fact": "q307_done", "tags": ["pl-main", "ending", "songbird"]},
      # PL minor side quests
      {"id": "mq301",  "name": "Balls to the Wall",                               "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq303",  "name": "Dazed and Confused",                              "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq304",  "name": "Run This Town",                                   "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq305",  "name": "Shot by Both Sides",                              "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
      {"id": "mq306",  "name": "No Easy Way Out",                                 "dep": "during PL",  "tags": ["pl-side", "dogtown"]},
    ],
  },

  # ── PHANTOM LIBERTY — SIDE CONTENT ───────────────────────────────────────────
  {
    "id": "pl_side", "label": "PL Side Quests & Activities", "color": "#9966ff", "icon": "◈",
    "tags": ["phantom-liberty", "dlc", "side-job"],
    "quests": [
      {"id": "wst_ep1_04",    "name": "Addicted to Chaos",              "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_05",    "name": "Go Your Own Way",                "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_09",    "name": "One Way or Another",             "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_11",    "name": "New Person, Same Old Mistakes",  "tags": ["dogtown", "pl-side"]},
      {"id": "wst_ep1_21",    "name": "Water Runs Dry",                 "tags": ["dogtown", "pl-side"]},
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
      {"id": "mq036",  "name": "Sweet Dreams",                             "dep": "Act 2",                    "reward_key": "mq036_money_back", "tags": ["minor"]},
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

# ── Life path filtering ────────────────────────────────────────────────────────
# Maps metadata.lifePath values → tag string used on life-path-exclusive quests
LIFE_PATH_TAG: dict[str, str] = {
    "Corporate": "corpo",
    "Nomad":     "nomad",
    "StreetKid": "street-kid",
}

# ── Suppress set ──────────────────────────────────────────────────────────────
# IDs that appear in finishedQuests but should NOT trigger the "Uncatalogued" section
SUPPRESS_IDS: set[str] = (
    # Parent-group flags — auto-set when child quests finish; tracked indirectly
    {"q000", "q001", "q306"}
    # Dogtown airdrop sandbox activities — unnamed loot-crate events
    | {"sa_ep1_31","sa_ep1_32","sa_ep1_33","sa_ep1_34","sa_ep1_35",
       "sa_ep1_37","sa_ep1_38","sa_ep1_39","sa_ep1_303","sa_ep1_306"}
    # Duplicate IDs — same quest stored under two IDs in finishedQuests
    | {"we_ep1_01", "we_ep1_05"}  # duplicates of mq301 / mq304
)

# ── Wiki alias overrides ───────────────────────────────────────────────────────
# No _WIKI_ALIASES dict exists in the source — wiki logic is handled inline
# in the HTML/JS template within tracker_local.py.

# ── Weapon gate data ───────────────────────────────────────────────────────────
# Maps _weapon_* IDs to the quest that gates acquisition; used by cyberpunk_tracker.py
WEAPON_GATES: dict[str, dict] = {
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

# Maps mission names → quest IDs; used by cyberpunk_tracker.py for Sheets sync
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

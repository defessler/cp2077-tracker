"""
tracker_engine.py — Game-agnostic tracker engine.

Provides the core logic for building catalog completion data and rendering
the HTML dashboard. Designed to work with any game by supplying:
  - A quest catalog (list of category dicts, each with a 'quests' list)
  - A SaveData dict (produced by a game-specific save adapter)
  - Game metadata (title, wiki base URL)

SaveData contract (keys the engine reads):
  finished_quests: list[str]   — completed quest/activity IDs
  active_facts:    list[str]   — named flag IDs that are non-zero
  quest_rewards:   list[str]   — reward keys from aggregator nodes
  completed_at:    dict[str,str] — quest_id -> "DD Mon · HH:MM"
  manual_results:  dict[str,bool] — _prefixed IDs -> found/not-found
  life_path:       str         — player life path / class (optional)
  choices:         dict[str,bool] — display flags for sidebar (optional)
  (plus any display fields: name, level, play_time, etc.)

Quest catalog schema (per category):
  id, label, color, icon        — required
  show_wiki: bool               — default True; False suppresses wiki links
  note: str                     — optional note shown above quest list
  tags: list[str]               — applied to all quests in category
  quests: list of quest dicts:
    id: str                     — display ID (also used for completion lookup)
    name: str                   — display name
    check_id: str               — override ID for finishedQuests lookup
    check_fact: str             — FactsDB fact name that signals completion
    reward_key: str             — reward aggregator key signaling completion
    dep: str                    — prerequisite description (display only)
    wiki: None|False|str        — None=auto-generate, False=suppress, str=slug
    tags: list[str]             — quest-level tags

Manual tracking convention:
  Quest IDs starting with '_' are treated as manually-tracked items (e.g.
  collectibles). Their completion state comes from save['manual_results'].
  These rows are rendered as toggleable in the UI via localStorage.

Adding another game:
  1. Create mygame_catalog.py — define QUEST_CATALOG, SUPPRESS_IDS,
     LIFE_PATH_TAG (or None), and any game-specific constants.
  2. Create mygame_save.py    — implement load_latest_save() and parse_save()
     returning a SaveData dict matching the contract above.
  3. Create mygame_local.py  — thin entry point (see tracker_local.py).
"""
from __future__ import annotations

import json
from pathlib import Path


# ── Core logic ─────────────────────────────────────────────────────────────────

def quest_done(quest_id: str,
               finished: set[str],
               facts: set[str],
               check_fact: str | None = None,
               reward_key: str | None = None,
               quest_rewards: set[str] | None = None,
               manual_results: dict[str, bool] | None = None) -> bool:
  """Return True if the quest/activity is considered complete."""
  # Manual override always wins — used for items/quests with no detectable save state
  if manual_results and manual_results.get(quest_id):
    return True
  if quest_id.startswith("_"):
    return False  # manual-only items default to not-found
  if check_fact:
    return check_fact in facts
  if reward_key and quest_rewards and reward_key in quest_rewards:
    return True
  return quest_id in finished


def build_catalog_data(save: dict,
                       catalog: list[dict],
                       life_path_tags: dict[str, str] | None = None,
                       suppress_ids: set[str] | None = None,
                       branch_tags: set[str] | None = None) -> list[dict]:
  """
  Build per-category completion data from save state and catalog.

  Returns a list of category dicts suitable for JSON serialisation and
  passed to generate_html(). An 'Uncatalogued' category is appended when
  finished_quests contains IDs not covered by the catalog or suppress_ids.

  Args:
    save:           SaveData dict from the game adapter.
    catalog:        Quest catalog (list of category dicts).
    life_path_tags: Maps save key values to tag strings so quests tagged
                    with a path tag are skipped for non-matching players.
                    Checked against both save['life_path'] and save['pl_path'].
                    E.g. {"Corporate": "corpo", "Nomad": "nomad",
                          "songbird": "songbird", "reed": "reed"}.
    suppress_ids:   Set of quest IDs to exclude from the 'Uncatalogued'
                    category (parent flags, duplicate IDs, sandbox IDs, etc.).
  """
  finished      = set(save["finished_quests"])
  facts         = set(save["active_facts"])
  quest_rewards = set(save.get("quest_rewards", []))
  completed_at  = save.get("completed_at", {})
  manual_results = save.get("manual_results", {})

  all_lp_tags: set[str] = set()
  player_tags: set[str] = set()
  if life_path_tags:
    all_lp_tags = set(life_path_tags.values())
    for save_key in ("life_path", "pl_path"):
      tag = life_path_tags.get(save.get(save_key, ""), "")
      if tag:
        player_tags.add(tag)

  catalogued_ids: set[str] = set()
  result: list[dict] = []

  for cat_idx, cat in enumerate(catalog):
    quests_out: list[dict] = []
    for q_idx, q in enumerate(cat["quests"]):
      q_tags       = set(q.get("tags", []))
      lp_on_quest  = q_tags & all_lp_tags
      is_uncompletable = bool(q.get("uncompletable"))

      # Path-exclusive quests: show as branch if in branch_tags, else skip
      branch_label = ""
      if lp_on_quest and not (lp_on_quest & player_tags):
        if branch_tags and (lp_on_quest & branch_tags):
          branch_label = next(iter(lp_on_quest & branch_tags)).title() + " path"
        else:
          continue  # hide life-path prologue quests entirely

      check_id   = q.get("check_id", q["id"])
      check_fact = q.get("check_fact")
      reward_key = q.get("reward_key")
      applicable = not branch_label
      done = False if (not applicable or is_uncompletable) else quest_done(
          check_id, finished, facts, check_fact, reward_key, quest_rewards, manual_results)
      catalogued_ids.add(check_id)
      catalogued_ids.add(q["id"])

      ts_key = check_fact if check_fact else check_id
      quests_out.append({
        "id":             q["id"],
        "name":           q["name"],
        "dep":            q.get("dep", ""),
        "wiki":           q.get("wiki"),
        "tags":           list(dict.fromkeys(q.get("tags", []) + cat.get("tags", []))),
        "done":           done,
        "seq":            q_idx,
        "cat_seq":        cat_idx * 1000,
        "manual":         q["id"].startswith("_"),
        "completed_at":   completed_at.get(ts_key, ""),
        "applicable":     applicable,
        "branch":         branch_label,
        "missed":         bool(q.get("missed")),
        "uncompletable":  is_uncompletable,
        "note":           q.get("note", ""),
      })

    # Only count quests that are applicable and completable in totals
    total     = sum(1 for q in quests_out if q["applicable"] and not q["uncompletable"])
    completed = sum(1 for q in quests_out if q["done"] and q["applicable"] and not q["uncompletable"])
    result.append({
      "id":          cat["id"],
      "label":       cat["label"],
      "color":       cat["color"],
      "icon":        cat["icon"],
      "note":        cat.get("note", ""),
      "show_wiki":   cat.get("show_wiki", True),
      "wiki_prefix": cat.get("wiki_prefix", ""),
      "wiki_url":    cat.get("wiki_url", ""),
      "completed":   completed,
      "total":       total,
      "pct":         round(100 * completed / total) if total else 0,
      "quests":      quests_out,
    })

  # Append uncatalogued quests found in the save but not in the catalog
  if suppress_ids is None:
    suppress_ids = set()
  extra = sorted(
    q for q in finished
    if q not in catalogued_ids
    and not q.startswith("_")
    and q not in suppress_ids
  )
  if extra:
    result.append({
      "id": "uncatalogued", "label": "Uncatalogued", "color": "#555",
      "icon": "?", "note": "", "show_wiki": False,
      "completed": len(extra), "total": len(extra), "pct": 100,
      "quests": [
        {"id": q, "name": q, "tags": ["uncatalogued"], "done": True,
         "seq": i, "cat_seq": 999000, "manual": False,
         "completed_at": "", "dep": "", "wiki": False}
        for i, q in enumerate(extra)
      ],
    })

  return result


def generate_html(save: dict,
                  catalog_data: list[dict],
                  output_file: Path,
                  game_title: str = "Tracker",
                  wiki_base_url: str = "") -> None:
  """Render the HTML dashboard and write it to output_file."""
  payload = {
    "save":    save,
    "catalog": catalog_data,
    "meta":    {"wiki_base": wiki_base_url, "title": game_title},
  }
  html = HTML_TEMPLATE.replace("__TITLE__", game_title).replace(
    "__DATA__", json.dumps(payload, ensure_ascii=False)
  )
  output_file.write_text(html, encoding="utf-8")


# ── HTML template ──────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
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

/* ── choices ── */
.choice-row{display:flex;justify-content:space-between;align-items:center;padding:2px 0;font-size:12px;gap:4px}
.choice-label{color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.choice-label a{color:var(--muted);text-decoration:none}
.choice-label a:hover{color:var(--cyan);text-decoration:underline}
.choice-val{font-size:10px;letter-spacing:.5px;flex-shrink:0;cursor:pointer;user-select:none;padding:1px 5px;border-radius:2px;border:1px solid transparent;transition:filter .2s}
.choice-val.spoiler{filter:blur(4px);background:#1a1a2a;border-color:#2a2a3a}
.choice-val.spoiler:hover{filter:blur(2px)}
.choice-val.c-yes{color:var(--green)}
.choice-val.c-no{color:var(--muted)}
.choice-val.c-pending{color:#555;font-style:italic}

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
.cat-card.cat-complete{border-color:#1a3d1a}
.cat-card.cat-complete .mini-fill{box-shadow:0 0 4px currentColor}
.cat-card-head{display:flex;align-items:center;gap:6px;margin-bottom:6px}
.cat-icon{font-size:14px}
.cat-label{font-size:11px;letter-spacing:1px;text-transform:uppercase;font-weight:bold;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cat-done-check{font-size:12px;color:#3a8a3a;flex-shrink:0}
.cat-counts{font-size:10px;color:var(--muted);letter-spacing:1px}
.cat-counts b{color:var(--text)}
.mini-bar{height:3px;background:#1a1a2a;border-radius:1px;overflow:hidden;margin-top:4px}
.mini-fill{height:100%;border-radius:1px}

/* ── quest list ── */
.quest-panel{background:var(--panel);border:1px solid var(--border);border-radius:2px;margin-bottom:16px}
.panel-complete{border-color:#1a3d1a}
.quest-panel-head{padding:10px 14px;display:flex;align-items:center;gap:8px;border-bottom:1px solid var(--border)}
.quest-panel-title{font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:bold}
.quest-panel-sub{font-size:10px;color:var(--muted);margin-left:auto;letter-spacing:1px}

.quest-row{display:flex;align-items:flex-start;gap:10px;padding:6px 14px;border-bottom:1px solid #0a0a16;transition:background .1s}
.quest-row:last-child{border-bottom:none}
.quest-row:hover{background:#0c0c1a}
.quest-row.hidden{display:none}
/* Locked states — hidden unless Locked toggle active */
.quest-row.q-branch{opacity:.5;border-left:3px solid #3a2a6a}
.quest-row.q-missed{opacity:.5;border-left:3px solid #6a3a10}
.quest-row.q-uncompletable{opacity:.45;border-left:3px solid #5a1a1a}
.quest-row.q-uncompletable .q-name{text-decoration:line-through}
/* State badges */
.q-state-label{font-size:9px;letter-spacing:.8px;text-transform:uppercase;padding:1px 4px;border-radius:2px;margin-left:4px;vertical-align:middle}
.q-branch-label{color:#8866cc;background:#0d0a22;border:1px solid #3a2a6a}
.q-missed-label{color:#cc7733;background:#1a0c00;border:1px solid #6a3a10}
.q-unc-label{color:#cc3344;background:#1a0808;border:1px solid #5a1a1a}
/* Check icons */
.q-check{font-size:14px;line-height:1;margin-top:1px;flex-shrink:0}
.q-done .q-check{color:var(--green)}
.q-todo .q-check{color:#333}
.q-branch .q-check{color:#5544aa}
.q-missed .q-check{color:#aa6622}
.q-uncompletable .q-check{color:#882233}
.q-info{flex:1;min-width:0}
.q-name{font-size:12px;color:var(--text);line-height:1.3}
.q-todo .q-name{color:var(--muted)}
.q-dep{font-size:9px;color:#3a6a8a;letter-spacing:.3px;margin-left:6px;opacity:.8;cursor:pointer;transition:filter .2s;user-select:none}
.q-dep.spoiler{filter:blur(3px);color:#2a4a6a}
.q-dep.spoiler:hover{filter:blur(1.5px)}
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

/* ── manual (collectible) rows ── */
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
  <h1>__TITLE__</h1>
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
      <div class="toolbar-sep"></div>
      <button class="filter-btn" id="lockedToggle">Locked</button>
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
    <div class="s-title">Choices <span style="font-size:9px;color:#445;font-weight:normal;letter-spacing:0">(click to reveal)</span></div>
    ${Object.entries(s.choices||{}).map(([k,v])=>{
      const wikiBase = (DATA.meta && DATA.meta.wiki_base) || '';
      // v is [done, yes_label, no_label, wiki_slug] or legacy bool
      const arr = Array.isArray(v);
      const done = arr ? v[0] : v;
      const yesLabel = arr ? v[1] : 'Yes';
      const noLabel  = arr ? v[2] : 'No';
      const slug     = arr ? v[3] : null;
      const label    = slug && wikiBase
        ? `<a href="${wikiBase}${encodeURIComponent(slug)}" target="_blank" onclick="event.stopPropagation()" title="Open wiki">${k}</a>`
        : k;
      const isPending = !done && (yesLabel === 'Saved' || noLabel === 'Pending' || yesLabel === 'Done' || yesLabel === 'Chosen' || yesLabel === 'Paid');
      const valClass = done ? 'c-yes' : isPending ? 'c-pending' : 'c-no';
      const valText  = done ? yesLabel : noLabel;
      return `<div class="choice-row">
        <span class="choice-label">${label}</span>
        <span class="choice-val spoiler ${valClass}" onclick="this.classList.toggle('spoiler')" title="Click to reveal">${valText}</span>
      </div>`;
    }).join('')}
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
    <div class="cat-card${activeCategory===c.id?' active':''}${c.pct===100?' cat-complete':''}" data-cat="${c.id}">
      <div class="cat-card-head">
        <span class="cat-icon" style="color:${c.color}">${c.icon}</span>
        <span class="cat-label" style="color:${c.color}">${c.label}</span>
        ${c.pct===100?'<span class="cat-done-check">&#9745;</span>':''}
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
  return arr;
}

// ── Manual collectible tracking (localStorage) ────────────────────────────────
function applyManualOverrides() {
  const stored = JSON.parse(localStorage.getItem('tracker_weapons') || '{}');
  DATA.catalog.forEach(cat => {
    let hasManual = false;
    cat.quests.forEach(q => {
      if (q.manual) {
        if (q.id in stored) q.done = stored[q.id] === true;
        hasManual = true;
      }
    });
    if (hasManual) {
      cat.completed = cat.quests.filter(q => q.done).length;
      cat.pct = cat.total ? Math.round(100 * cat.completed / cat.total) : 0;
    }
  });
}

function toggleManual(qid) {
  const stored = JSON.parse(localStorage.getItem('tracker_weapons') || '{}');
  const q = DATA.catalog.flatMap(c => c.quests).find(q => q.id === qid);
  const cur = q ? q.done : (stored[qid] === true);
  stored[qid] = !cur;
  localStorage.setItem('tracker_weapons', JSON.stringify(stored));
  applyManualOverrides();
  renderOverall();
  renderCards();
  renderQuestPanels();
}

// ── Quest panels ──────────────────────────────────────────────────────────────
function renderQuestPanels() {
  const cats = activeCategory==='all' ? DATA.catalog : DATA.catalog.filter(c=>c.id===activeCategory);
  const wikiBase = (DATA.meta && DATA.meta.wiki_base) || '';
  const panels = document.getElementById('questPanels');
  panels.innerHTML = cats.map(cat=>`
    <div class="quest-panel${cat.pct===100?' panel-complete':''}" data-panel="${cat.id}">
      <div class="quest-panel-head" style="border-left:3px solid ${cat.color}">
        <span style="color:${cat.color}">${cat.icon}</span>
        <span class="quest-panel-title" style="color:${cat.color}">${cat.label}</span>
        <span class="quest-panel-sub">${cat.completed}/${cat.total} · ${cat.pct}%${cat.pct===100?' <span style="color:#3a8a3a;margin-left:6px">&#9745; COMPLETE</span>':''}</span>
      </div>
      ${cat.note ? `<div class="q-panel-note">${cat.note}</div>` : ''}
      ${sortQuests(cat.quests).map(q=>{
        const dedup=[...new Set(q.tags)];
        const catWikiPrefix = cat.wiki_prefix || '';
        const catWikiUrl    = cat.wiki_url    || null;
        let wikiUrl = null;
        if (cat.show_wiki !== false && q.wiki !== false) {
          if (q.wiki && typeof q.wiki === 'string' && q.wiki.startsWith('http')) {
            wikiUrl = q.wiki;
          } else if (wikiBase) {
            if (q.wiki) {
              wikiUrl = wikiBase + encodeURIComponent(q.wiki);
            } else {
              const baseName = q.name.split('→')[0].split(' / ')[0].trim().replace(/\s*\([^)]*\)\s*$/, '').trim();
              if (baseName) wikiUrl = wikiBase + catWikiPrefix + encodeURIComponent(baseName.replace(/ /g,'_'));
            }
          }
          if (!wikiUrl && catWikiUrl) wikiUrl = catWikiUrl;
        }
        const isLocked = !!(q.branch || q.missed || q.uncompletable);
        const rowClass = q.done ? 'q-done'
          : q.branch        ? 'q-branch'
          : q.missed        ? 'q-missed'
          : q.uncompletable ? 'q-uncompletable'
          : 'q-todo';
        const checkIcon = q.done ? '✓'
          : q.branch        ? '⬡'
          : q.missed        ? '✗'
          : q.uncompletable ? '⊘'
          : '○';
        const extraLabel = q.branch
          ? `<span class="q-state-label q-branch-label">${q.branch}</span>`
          : q.missed        ? `<span class="q-state-label q-missed-label">Missed</span>`
          : q.uncompletable ? `<span class="q-state-label q-unc-label">${q.note||'Uncompletable'}</span>`
          : '';
        return `<div class="quest-row ${rowClass}" data-done="${q.done}" data-id="${q.id}" data-name="${q.name.toLowerCase()}" data-tags="${dedup.join(' ')}" data-manual="${q.manual||false}" data-locked="${isLocked}">
          <span class="q-check">${checkIcon}</span>
          <div class="q-info">
            <div class="q-name">${q.name}${extraLabel}${q.dep?`<span class="q-dep spoiler" onclick="this.classList.toggle('spoiler')" title="Click to reveal">▸ ${q.dep}</span>`:''}${wikiUrl?` <a class="q-wiki" href="${wikiUrl}" target="_blank" title="Open on wiki" onclick="event.stopPropagation()">WIKI ↗</a>`:''}<button class="q-report" onclick="reportIssue('${q.id}','${cat.label.replace(/'/g,"\\'")}','${q.name.replace(/'/g,"\\'")}',${q.done},event)" title="Report issue">⚑ REPORT</button></div>
            <div class="q-id">${q.id}${q.done&&q.completed_at?`<span class="q-ts">${q.completed_at}</span>`:''}</div>
            <div class="q-tags">${dedup.map(t=>`<span class="q-tag t-${t}" data-tag="${t}">${t}</span>`).join('')}</div>
          </div>
        </div>`;
      }).join('')}
    </div>`).join('');

  panels.querySelectorAll('.q-tag').forEach(tag=>{
    tag.addEventListener('click', e=>{
      e.stopPropagation();
      document.getElementById('searchBox').value = tag.dataset.tag;
      applyFilters();
    });
  });

  panels.querySelectorAll('.quest-row[data-manual="true"]').forEach(row=>{
    row.addEventListener('click', e=>{
      if (e.target.closest('a,button,.q-tag')) return;
      toggleManual(row.dataset.id);
    });
  });

  applyFilters();
}

// ── Filters ───────────────────────────────────────────────────────────────────
let activeFilter = 'all';
let showLocked   = false;

function applyFilters() {
  const q    = document.getElementById('searchBox').value.toLowerCase().trim();
  const rows = document.querySelectorAll('.quest-row');
  let vis = 0;
  rows.forEach(row=>{
    const isLocked = row.dataset.locked === 'true';
    // Hide locked rows unless toggle active
    if (isLocked && !showLocked) { row.classList.add('hidden'); return; }
    const filterOk = activeFilter==='all'
      || (activeFilter==='done' && row.dataset.done==='true')
      || (activeFilter==='todo' && row.dataset.done==='false' && !isLocked);
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
  const initHash = location.hash.slice(1);
  if (initHash && DATA.catalog.some(c => c.id === initHash)) {
    activeCategory = initHash;
  }
  renderSidebar();
  renderOverall();
  renderCards();
  renderQuestPanels();

  document.querySelectorAll('.filter-btn[data-f]').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('.filter-btn[data-f]').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      activeFilter = b.dataset.f;
      applyFilters();
    });
  });

  document.getElementById('lockedToggle').addEventListener('click', b=>{
    showLocked = !showLocked;
    b.currentTarget.classList.toggle('active', showLocked);
    renderQuestPanels();
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
const QUEUE_KEY = 'tracker_reports';

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
    `Quest: ${name}\nID: ${id}\nCategory: ${cat}\nStatus: ${status}\nSave: ${save}`;
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
  if (!q.find(r => r.id === d.id && r.desc === desc)) {
    q.push({id: d.id, cat: d.cat, name: d.name, status: d.status, save: d.save, desc, ts: Date.now()});
    saveQueue(q);
  }
  const el = document.getElementById('rAddConfirm');
  el.style.opacity = '1';
  setTimeout(()=>{ el.style.opacity='0'; closeReport(); }, 900);
}

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
  const title = (DATA.meta && DATA.meta.title) || 'TRACKER';
  const lines = [
    `[${title.toUpperCase()} BUG REPORTS] — ${q.length} issue${q.length>1?'s':''}`,
    `Save: ${save}`,
    '',
    ...q.map((r, i) => [
      `${i+1}. Quest: ${r.name}`,
      `   ID: ${r.id}`,
      `   Category: ${r.cat}`,
      `   Status: ${r.status}`,
      `   Issue: ${r.desc}`,
    ].join('\n')),
  ];
  navigator.clipboard.writeText(lines.join('\n')).then(()=>{
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

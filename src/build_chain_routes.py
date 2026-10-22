"""Build globe/data/chain_routes.json, the file behind the Chain routes layer on the globe.

Why this file exists: references/chain_routes.json is the curated input (stages, places,
routes and their source ids). The page should not have to look anything up, so this
script copies each route's two places into the route and replaces each source id with
that source's details from the ledger (references/sources.json). It never changes either input.

It refuses to build (exit code 1, nothing written) when a route is not backed properly:
no source ids, a source id missing from the ledger, an unknown stage, a missing place,
or a latitude / longitude out of range. A route without a source never reaches the globe.

Run it after every change to references/chain_routes.json or to the ledger.
Run from the project root:  python3 src/build_chain_routes.py
"""

import json
import os
import sys

# Why import from config: the project root and the ledger path are defined once, in src/config.py.
from config import PROJECT_ROOT, PATHS

# These two paths should move into PATHS in src/config.py. That file has other
# unfinished edits at the moment, so they stay here until those are committed.
CURATED = os.path.join(PROJECT_ROOT, "references", "chain_routes.json")
TARGET = os.path.join(PROJECT_ROOT, "globe", "data", "chain_routes.json")

# The ledger has no field for a page's date or for who publishes it, so both are
# recorded here, once, for the route sources only. Dates are as shown on each page
# (checked 22 Oct 2026); None means the card shows no date for that source.
# AGENCIES = a public body. TRADE PRESS = a news or trade article (the ledger type "trade_press").
SOURCE_INFO = {
    "src_cbi_eu_coffee_trade":        {"date": "2026-02-12", "tag": "AGENCIES"},
    "src_cbi_nl_coffee_market":       {"date": "2026-02-11", "tag": "AGENCIES"},
    "src_stonex_santos_2026":         {"date": "2026-07-29", "tag": "TRADE PRESS"},
    "src_datamar_brazil_2026":        {"date": "2026-04-15", "tag": "TRADE PRESS"},
    "src_stonex_colombia_ports_2021": {"date": "2021-09-15", "tag": "TRADE PRESS"},
    "src_gcr_indonesia_coffee":       {"date": None, "tag": "TRADE PRESS"},  # Rizki, 22 Oct 2026: show no date
}

# Why a cut-off year: a figure or page from before this year is drawn as dated on the card.
DATED_BEFORE = 2023


# ---------- the terminal look (rail, diamonds), same as build_references_panel.py ----------
DIM, RED, RESET = "\033[2m", "\033[31m", "\033[0m"


def say_step(label, summary, ok=True):
    print("│")
    if ok:
        print(f"◇  {label}  {DIM}{summary}{RESET}")
    else:
        print(f"◆  {label}")
        print(f"│  {RED}{summary}{RESET}")


def place_problem(route_id, end, place_id, places):
    """Return one line saying what is wrong with a route's place, or None if it is fine."""
    if place_id not in places:
        return f"route {route_id}: '{end}' place '{place_id}' is missing from places"
    p = places[place_id]
    # Why check the range: a swapped or mistyped coordinate would draw the line somewhere else.
    if not isinstance(p.get("lat"), (int, float)) or not -90 <= p["lat"] <= 90:
        return f"route {route_id}: place '{place_id}' has lat {p.get('lat')} (must be -90 to 90)"
    if not isinstance(p.get("lng"), (int, float)) or not -180 <= p["lng"] <= 180:
        return f"route {route_id}: place '{place_id}' has lng {p.get('lng')} (must be -180 to 180)"
    return None


def place_out(place_id, p):
    """One place as the page needs it. The label is the name up to its first bracket."""
    label = p["name"].split(" (")[0]
    if p.get("approx"):
        label += " (approx.)"  # the point is the middle of a growing area, not a farm
    return {"id": place_id, "name": p["name"], "label": label, "kind": p["kind"],
            "lat": p["lat"], "lng": p["lng"], "approx": bool(p.get("approx"))}


# Why check first: a clear message is easier to act on than a traceback.
for path in (CURATED, PATHS["sources_ledger"]):
    if not os.path.exists(path):
        sys.exit(f"Stopped: {path} was not found")

with open(CURATED, encoding="utf-8") as f:
    curated = json.load(f)
with open(PATHS["sources_ledger"], encoding="utf-8") as f:
    ledger = {s["source_id"]: s for s in json.load(f)}

stages, places = curated["stages"], curated["places"]
print("┌  Build the Chain routes layer")
say_step("Read", f"{len(curated['routes'])} routes, {len(places)} places, {len(stages)} stages, {len(ledger)} ledger sources")

problems = []
routes = []
for r in curated["routes"]:
    rid = r.get("id", "(no id)")
    found = []  # problems with this route only

    if r.get("stage") not in stages:
        found.append(f"route {rid}: unknown stage '{r.get('stage')}'")
    for end in ("from", "to"):
        line = place_problem(rid, end, r.get(end), places)
        if line:
            found.append(line)
    if not r.get("source_ids"):
        found.append(f"route {rid}: no source_ids")
    for sid in r.get("source_ids", []):
        if sid not in ledger:
            found.append(f"route {rid}: source '{sid}' is not in references/sources.json")
        elif sid not in SOURCE_INFO:
            found.append(f"route {rid}: source '{sid}' has no date and tag in SOURCE_INFO")
        elif (SOURCE_INFO[sid]["tag"] == "TRADE PRESS") != (ledger[sid]["type"] == "trade_press"):
            found.append(f"route {rid}: source '{sid}' tag {SOURCE_INFO[sid]['tag']} does not match ledger type {ledger[sid]['type']}")
    if "figure" in r and not r["figure"].get("year"):
        found.append(f"route {rid}: the figure has no year")
    # Why only true or false: the card shows an ESTIMATE badge when it is true, so a typo must not slip through.
    if "figure" in r and r["figure"].get("estimate", False) not in (True, False):
        found.append(f"route {rid}: estimate must be true or false, not {r['figure']['estimate']!r}")

    if found:
        problems.extend(found)
        continue  # a route with a problem is never added

    sources = []
    for sid in r["source_ids"]:
        s, info = ledger[sid], SOURCE_INFO[sid]
        sources.append({"id": sid, "title": s["title"], "publisher": s["publisher_or_author"],
                        "url": s["url"], "date": info["date"], "tag": info["tag"],
                        "dated": bool(info["date"]) and int(info["date"][:4]) < DATED_BEFORE})
    figure = None
    if "figure" in r:
        figure = dict(r["figure"], dated=r["figure"]["year"] < DATED_BEFORE)  # "estimate" is passed through as given

    routes.append({"id": rid, "stage": r["stage"],
                   "from": place_out(r["from"], places[r["from"]]),
                   "to": place_out(r["to"], places[r["to"]]),
                   "figure": figure, "note": r.get("note"),
                   "illustration": bool(r.get("illustration")), "sources": sources})

# Why stop instead of writing the good routes: a half-built file would hide the problem.
if problems:
    for line in problems:
        say_step("Not built", line, ok=False)
    print("│")
    print(f"└  Stopped: {len(problems)} problem(s), nothing written")
    sys.exit(1)

# Count per stage, in the order of the stages block
counts = {k: sum(1 for r in routes if r["stage"] == k) for k in stages}
say_step("Per stage", " · ".join(f"{k} {n}" for k, n in counts.items()))
dated = [r["id"] for r in routes if (r["figure"] and r["figure"]["dated"]) or any(s["dated"] for s in r["sources"])]
say_step("Dated (before %d)" % DATED_BEFORE, ", ".join(dated) or "none")

# Why makedirs: globe/data/ may not exist yet on a fresh clone.
os.makedirs(os.path.dirname(TARGET), exist_ok=True)
with open(TARGET, "w", encoding="utf-8") as f:
    json.dump({"note": curated["note"], "dated_before": DATED_BEFORE, "stages": stages, "routes": routes},
              f, ensure_ascii=False, indent=1)
    f.write("\n")

print("│")
print(f"└  Wrote {len(routes)} routes to globe/data/chain_routes.json")

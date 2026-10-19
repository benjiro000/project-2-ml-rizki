"""Apply Rizki's publishing decisions to the literature cards.

Why this file exists: the Scout's literature_cards.json stays exactly as the
Scout wrote it. The globe reads literature_cards.approved.json instead, which
this script rebuilds from the Scout's file plus the rules below. To change a
decision, change its rule and run the script again.

Run from the project root:  python3 src/approve_literature.py
"""

import json
import os
import sys

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS

# Rizki's decisions of 19 Oct 2026, after Reviewer run 3. One line per rule, with the reason.
RULES = [
    {"action": "drop_source", "src": "src_irchad2026_comoros", "why": "Comoros paper: one plantation only, and its table prints protein of about 95 %"},
    {"action": "drop_row", "country": "UGA", "list": "composition", "compound": "caffeine", "why": "1.94-3.0 g/100 g is above the paper's own Arabica range (0.9-1.5 %)"},
    {"action": "set_processing", "country": "UGA", "value": "lab-dried", "why": "the Ugandan cherries were air-dried in the lab, which says nothing about farm processing"},
]


def label(country, list_name, item):
    """Short name for one card item, for the printed log."""
    name = item.get("compound") or item.get("type") or item.get("name")
    return f"{country} {list_name}: {name}"


source = PATHS["literature_cards"]
target = PATHS["literature_cards_approved"]

# Why check first: a clear message is easier to act on than a traceback.
if not os.path.exists(source):
    sys.exit(f"Stopped: the literature cards were not found at {source}")

with open(source, encoding="utf-8") as f:
    cards = json.load(f)

for rule in RULES:
    matches = 0
    for country, card in cards["countries"].items():
        for list_name, items in card.items():
            kept = []
            for item in items:
                if rule["action"] == "drop_source" and item["src"] == rule["src"]:
                    print(f"removed  {label(country, list_name, item)}  ({rule['why']})")
                    matches += 1
                    continue
                if (rule["action"] == "drop_row" and country == rule["country"]
                        and list_name == rule["list"] and item.get("compound") == rule["compound"]):
                    print(f"removed  {label(country, list_name, item)}  ({rule['why']})")
                    matches += 1
                    continue
                if (rule["action"] == "set_processing" and country == rule["country"]
                        and list_name == "composition"):
                    print(f"changed  {label(country, list_name, item)}: processing "
                          f"{item['processing']} -> {rule['value']}  ({rule['why']})")
                    item["processing"] = rule["value"]
                    matches += 1
                kept.append(item)
            card[list_name] = kept

    # Why drop it from the card's source list too: no item points to it any more.
    # It stays in the ledger (references/sources.json), which this script never touches.
    if rule["action"] == "drop_source" and rule["src"] in cards["sources"]:
        del cards["sources"][rule["src"]]
        print(f"removed  source {rule['src']} from the card's source list  ({rule['why']})")

    # Why stop here: a rule that matches nothing means the cards changed and the rule is out of date.
    if matches == 0:
        sys.exit(f"Stopped: this rule matched nothing, please check it: {rule}")

# Why: a country with nothing left would show an empty card on the globe.
for country in list(cards["countries"]):
    if all(len(items) == 0 for items in cards["countries"][country].values()):
        del cards["countries"][country]
        print(f"removed  country {country} (no items left)")

# Why check: every item must still point to a source the card can show.
for country, card in cards["countries"].items():
    for list_name, items in card.items():
        for item in items:
            if item["src"] not in cards["sources"]:
                sys.exit(f"Stopped: {label(country, list_name, item)} uses {item['src']}, which is not in the source list")

# Why record the rules in the file: whoever opens it later can see what was changed and why.
cards["approval"] = {"approved_by": "Rizki", "date": "2026-10-19",
                     "rules": [rule["why"] for rule in RULES]}

with open(target, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

countries = cards["countries"].values()
print(f"Wrote {target}")
print(f"countries: {len(cards['countries'])}, "
      f"composition rows: {sum(len(c.get('composition', [])) for c in countries)}, "
      f"processing items: {sum(len(c.get('processing_fine', [])) for c in countries)}, "
      f"varieties: {sum(len(c.get('varieties', [])) for c in countries)}, "
      f"sources: {len(cards['sources'])}")

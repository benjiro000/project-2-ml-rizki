"""Build the source list that the References panel on the globe shows.

Why this file exists: references/sources.json (the ledger) is the single
master and keeps every source. The panel should only show the sources
behind the globe's content, not the ones about how we built the project.
This script reads the ledger, leaves out the ids in HIDE, and writes
globe/data/sources.json. It never changes the ledger.

Run it after every change to the ledger.
Run from the project root:  python3 src/build_references_panel.py
"""

import json
import os
import sys

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS

# Rizki's decision of 19 Oct 2026: these sources are about how we built the
# project (agent design, course template, tools' docs, a closed mirror site),
# not about coffee, so the panel leaves them out. They stay in the ledger.
HIDE = [
    "src_12factor_agents",        # agent design principles
    "src_ironhack_p2_template",   # the course template we forked
    "src_humanlayer_docs_home",   # HumanLayer docs: how we run the agents
    "src_humanlayer_first_task",
    "src_humanlayer_workflows",
    "src_humanlayer_skills_ref",
    "src_hatchworks_n8n",         # n8n blog post: how we orchestrate the agents
    "src_baselight_shutdown",     # announcement page of a closed dataset mirror
]

# Why watch these two types: new documentation or web pages may also be about
# the build. The script does not hide them by itself; it asks a human to decide.
BUILD_TYPES = ["documentation", "web_page"]


# ---------- the terminal look (rail, diamonds), same as build_country_facts.py ----------
DIM, RED, RESET = "\033[2m", "\033[31m", "\033[0m"


def say_step(label, summary, ok=True):
    print("│")
    if ok:
        print(f"◇  {label}  {DIM}{summary}{RESET}")
    else:
        print(f"◆  {label}")
        print(f"│  {RED}{summary}{RESET}")


source = PATHS["sources_ledger"]
target = PATHS["globe_sources"]

# Why check first: a clear message is easier to act on than a traceback.
if not os.path.exists(source):
    sys.exit(f"Stopped: the source ledger was not found at {source}")

with open(source, encoding="utf-8") as f:
    ledger = json.load(f)

print("┌  Build the References panel")
say_step("Read", f"{len(ledger)} sources from the ledger")

# Why check the HIDE list: a typo in an id would silently hide nothing.
ledger_ids = [s["source_id"] for s in ledger]
unknown = [i for i in HIDE if i not in ledger_ids]
if unknown:
    say_step("HIDE ids not in the ledger", ", ".join(unknown), ok=False)

# Keep every entry whose id is not in HIDE, in ledger order, unchanged
shown = [s for s in ledger if s["source_id"] not in HIDE]
say_step("Hidden", f"{len(ledger) - len(shown)} sources about how we built the project")

# Build-type entries that are still shown: list them for a human to decide
to_decide = [s["source_id"] for s in shown if s["type"] in BUILD_TYPES]
if to_decide:
    say_step("Documentation or web pages still shown, please decide", ", ".join(to_decide), ok=False)

# Count per type, in the order the types first appear (the panel groups the same way)
counts = {}
for s in shown:
    counts[s["type"]] = counts.get(s["type"], 0) + 1
say_step("Per type", " · ".join(f"{t} {n}" for t, n in counts.items()))

# Why makedirs: globe/data/ may not exist yet on a fresh clone.
os.makedirs(os.path.dirname(target), exist_ok=True)
with open(target, "w", encoding="utf-8") as f:
    json.dump(shown, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("│")
print(f"└  Wrote {len(shown)} sources to globe/data/sources.json")

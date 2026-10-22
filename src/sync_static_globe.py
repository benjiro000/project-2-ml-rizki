"""Copy the globe into static/globe/, the copy the Streamlit app (app.py) shows.

Why this file exists: Streamlit can only serve files from a folder called static
beside app.py, so the app shows a copy of globe/ and not globe/ itself. After every
change to the globe, run this script so the copy matches. It only overwrites the
files listed in FILES and never deletes anything.

Run it after every globe change, from the project root:  python3 src/sync_static_globe.py
"""

import filecmp
import os
import shutil
import sys

# Why import from config: the project root is defined once, in src/config.py.
from config import PROJECT_ROOT

SOURCE = os.path.join(PROJECT_ROOT, "globe")
TARGET = os.path.join(PROJECT_ROOT, "static", "globe")

# The same files that static/globe/ held when this script was written (22 Oct 2026)
FILES = [
    "coffee_globe.html",
    "country_card.js",
    os.path.join("data", ".gitkeep"),
    os.path.join("data", "chain_routes.json"),
    os.path.join("data", "country_facts.json"),
    os.path.join("data", "sources.json"),
]

# ---------- the terminal look (rail, diamonds), same as the build scripts ----------
DIM, RESET = "\033[2m", "\033[0m"

# Why check first: a missing file would leave the copy half updated.
missing = [f for f in FILES if not os.path.exists(os.path.join(SOURCE, f))]
if missing:
    sys.exit("Stopped: not found in globe/: " + ", ".join(missing))

print("┌  Copy the globe to static/globe/")
changed = 0
for f in FILES:
    src, dst = os.path.join(SOURCE, f), os.path.join(TARGET, f)
    # Why compare first: the summary then says which files really changed.
    same = os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False)
    if not same:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        changed += 1
    print("│")
    print(f"◇  {f}  {DIM}{'unchanged' if same else 'copied'}{RESET}")

print("│")
print(f"└  {changed} of {len(FILES)} files copied to static/globe/")

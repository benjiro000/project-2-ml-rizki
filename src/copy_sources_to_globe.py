"""Copy the source ledger to the folder the globe reads from.

Why this script exists: the website can only load files inside globe/,
but the ledger lives in references/. Run this after every change to the
ledger so the References panel on the globe stays up to date.

Run from the project root:  python3 src/copy_sources_to_globe.py
"""

import os
import shutil
import sys

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS

source = PATHS["sources_ledger"]
target = PATHS["globe_sources"]

# Why check first: a clear message is easier to act on than a traceback.
if not os.path.exists(source):
    sys.exit(f"Stopped: the source ledger was not found at {source}")

# Why makedirs: globe/data/ may not exist yet on a fresh clone.
os.makedirs(os.path.dirname(target), exist_ok=True)

# Why copy and not edit: the ledger in references/ stays the only original.
shutil.copyfile(source, target)
print(f"Copied {source}")
print(f"    to {target}")

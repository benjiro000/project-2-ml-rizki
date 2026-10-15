"""Project settings: the random seed and the file paths.

Why this file exists: the seed and the paths are defined once, here,
so notebooks and agents never hard-code them. To change one, change it
here and every notebook and agent picks it up.
"""

import os

# Why a fixed seed: the same split and the same model every run.
RANDOM_STATE = 42

# Why build from the project root: the paths work no matter which folder
# a notebook or script is started from. This file lives in src/, so the
# project root is one folder up.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Why logical names: agents only see these names, never real file paths.
PATHS = {
    "sources_ledger": os.path.join(PROJECT_ROOT, "references", "sources.json"),
    "raw_data": os.path.join(PROJECT_ROOT, "data", "raw"),
    "clean_data": os.path.join(PROJECT_ROOT, "data", "clean"),
    "model_dir": os.path.join(PROJECT_ROOT, "models"),
    "globe_data": os.path.join(PROJECT_ROOT, "globe", "data", "globe_data.json"),
    "globe_sources": os.path.join(PROJECT_ROOT, "globe", "data", "sources.json"),
    "prompts": os.path.join(PROJECT_ROOT, "prompts"),
    "profiles": os.path.join(PROJECT_ROOT, "references", "profiles"),
    "reviews": os.path.join(PROJECT_ROOT, "references", "reviews"),
}

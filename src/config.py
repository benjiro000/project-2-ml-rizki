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
    # Cleaning (agent 3): the two raw CQI files in, one clean table out.
    "raw_cqi_arabica": os.path.join(PROJECT_ROOT, "data", "raw", "ds_cqi_jldbc_2018", "arabica_data_cleaned.csv"),
    "raw_cqi_robusta": os.path.join(PROJECT_ROOT, "data", "raw", "ds_cqi_jldbc_2018", "robusta_data_cleaned.csv"),
    "clean_cqi": os.path.join(PROJECT_ROOT, "data", "clean", "cqi_clean.csv"),
    "sql_clean_cqi": os.path.join(PROJECT_ROOT, "src", "sql", "clean_cqi.sql"),
    "gate2_decisions": os.path.join(PROJECT_ROOT, "references", "gate2_decisions.json"),
    "cleaning_plan": os.path.join(PROJECT_ROOT, "references", "cleaning_plan.json"),
    "cleaning_report": os.path.join(PROJECT_ROOT, "references", "cleaning_report.json"),
    # Literature cards (Scout run 3): the Scout's file in, the approved copy the globe reads out.
    "literature_cards": os.path.join(PROJECT_ROOT, "references", "literature_cards.json"),
    "literature_cards_approved": os.path.join(PROJECT_ROOT, "references", "literature_cards.approved.json"),
    # First look: diagrams of the clean table, before any modelling.
    "first_look_figures": os.path.join(PROJECT_ROOT, "references", "figures", "first_look"),
}

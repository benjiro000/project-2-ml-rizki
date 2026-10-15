"""Your reusable functions live here.

The rule from the brief: Python logic goes in `.py` files, and the notebooks
hold the narrative. The moment a cell grows past a few lines, or you find
yourself pasting it a second time, move it here and call it from the notebook.

To use this module from a notebook in `notebooks/`:

    import sys
    sys.path.append("..")
    from src.functions import *

The four below are only there to show the shape. Rename them, change the
arguments, write your own. This is a starting point, not an interface you have
to implement.
"""

import hashlib
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MODELS = ROOT / "models"

RANDOM_STATE = 42


def load_data():
    """Read your raw file and apply the fixes that do not learn from the data."""
    pass


def build_preprocessor(numeric, categorical):
    """Return a ColumnTransformer that prepares each type of column."""
    pass


def compare_models(models, X, y, cv, scoring):
    """Cross-validate each model on the same folds and return a tidy table."""
    pass


def plot_errors(y_true, y_pred):
    """Show where the model goes wrong: a confusion matrix or the residuals."""
    pass


# ---------------------------------------------------------------------------
# Cleaning (agent 3). Rule-based only: nothing here learns from the data.
# Filling, scaling and encoding belong in the Pipeline, after the split.
# ---------------------------------------------------------------------------

SPECIES = ["arabica", "robusta"]


def file_fingerprint(path):
    """Return an MD5 fingerprint of a file.

    Why: if the fingerprint is the same before and after cleaning,
    the raw file was not changed.
    """
    with open(path, "rb") as file:
        return hashlib.md5(file.read()).hexdigest()


def count_columns(path):
    """Count the columns of a CSV file by reading only its header row."""
    # Why nrows=0: we only want the column names, not the values.
    return len(pd.read_csv(path, nrows=0).columns)


def kept_columns(decisions):
    """Return the columns kept at gate 2: features, target and profile."""
    return decisions["features"] + [decisions["target"]] + decisions["profile_columns"]


def robusta_columns(decisions):
    """Return the Robusta names of the kept columns.

    Strong matches are loaded under their Robusta name (the SQL renames them).
    Guessed matches (medium or weak) are not loaded at all: they stay empty.
    """
    robusta_name = {}
    guessed = []
    for match in decisions["robusta_column_matches"]:
        if "strong" in match["match"]:
            robusta_name[match["arabica_column"]] = match["robusta_column"]
        else:
            guessed.append(match["arabica_column"])
    return [robusta_name.get(column, column)
            for column in kept_columns(decisions) if column not in guessed]


def load_columns(path, columns):
    """Read only the given columns of a CSV file.

    Why usecols: the personal data columns are never loaded, not even
    for a moment (Cleaner hard rule 4).
    """
    return pd.read_csv(path, usecols=columns)


def stack_with_sql(arabica, robusta, sql_path):
    """Put both tables in an in-memory SQLite database and run the SQL file."""
    # Why ":memory:": the database only lives while this function runs,
    # so nothing is written to disk.
    connection = sqlite3.connect(":memory:")
    arabica.to_sql("arabica_raw", connection, index=False)
    robusta.to_sql("robusta_raw", connection, index=False)
    with open(sql_path) as file:
        query = file.read()
    stacked = pd.read_sql_query(query, connection)
    connection.close()
    return stacked


def count_per_species(df, mask):
    """Count the rows where mask is True, separately for each species."""
    counts = df.loc[mask, "species"].value_counts()
    # Why reindex: a species with no matching rows should show 0, not be missing.
    return counts.reindex(SPECIES, fill_value=0).to_dict()


def zero_to_missing(df, column):
    """Replace 0.0 with missing in one column. Return the table and the counts."""
    df = df.copy()
    mask = df[column] == 0
    counts = count_per_species(df, mask)
    df.loc[mask, column] = np.nan
    return df, counts


def above_to_missing(df, column, limit):
    """Replace values above a limit with missing. Return the table and the counts."""
    df = df.copy()
    mask = df[column] > limit
    counts = count_per_species(df, mask)
    df.loc[mask, column] = np.nan
    return df, counts


def rows_below(df, column, limit, show_columns):
    """List the rows where a column is below a limit, without changing them."""
    return df.loc[df[column] < limit, show_columns]


def drop_rows_equal(df, column, value):
    """Drop the rows where a column equals a value. Return the table and the counts."""
    mask = df[column] == value
    counts = count_per_species(df, mask)
    # Why reset_index: the clean table gets a simple 0, 1, 2, ... row index.
    return df.loc[~mask].reset_index(drop=True), counts


def step_line(name, rows_before, rows_after, columns_before, columns_after,
              values_changed, note=""):
    """Describe one cleaning step in one line (Cleaner hard rule 5)."""
    return {
        "step": name,
        "rows_before": int(rows_before),
        "rows_after": int(rows_after),
        "columns_before": int(columns_before),
        "columns_after": int(columns_after),
        "values_changed": int(values_changed),
        "note": note,
    }

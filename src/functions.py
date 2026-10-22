"""Your reusable functions live here.

The rule from the brief: Python logic goes in `.py` files, and the notebooks
hold the narrative. The moment a cell grows past a few lines, or you find
yourself pasting it a second time, move it here and call it from the notebook.

To use this module from a notebook in `notebooks/`:

    import sys
    sys.path.append("..")
    from src.functions import *
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


def mask_to_missing(df, column, mask):
    """Replace the values where mask is True with missing. Return the table and the counts.

    Why a mask: rules such as "between 0 and 0.05" or "Arabica only" are
    easy to read when the condition is written out where the rule is run.
    """
    df = df.copy()
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


# =====================================================================
# Project 2 functions, used by notebooks 01, 02 and 03
# =====================================================================

import os
from sklearn.model_selection import train_test_split, KFold, cross_validate
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer

TARGET = "Total.Cup.Points"
CATEGORICAL_FEATURES = ["Country.of.Origin", "Variety", "Processing.Method", "Color"]


def load_arabica(clean_dir):
    """Load the clean CQI table and keep the Arabica rows (the rows every notebook uses)."""
    clean = pd.read_csv(os.path.join(clean_dir, "cqi_clean.csv"))
    return clean[clean["species"] == "arabica"].copy()


def get_feature_columns(df):
    """Return (numeric columns, categorical columns) that the models may use."""
    defect_cols = [c for c in df.columns if "Defects" in c]
    numeric = ["Moisture", "altitude_mean_meters"] + defect_cols
    return numeric, CATEGORICAL_FEATURES


def split_once(df, random_state, test_size=0.2):
    """The ONE split of the project. Same seed, same rows, in every notebook."""
    numeric, categorical = get_feature_columns(df)
    X = df[numeric + categorical]
    y = df[TARGET]
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def make_cv(random_state, n_splits=5):
    """The same 5 folds for every model, so the comparison is fair."""
    return KFold(n_splits=n_splits, shuffle=True, random_state=random_state)


def _sum_across_columns(X):
    # adds up the columns of each row (used for the total number of defects)
    return np.asarray(X, dtype=float).sum(axis=1, keepdims=True)


def _total_defects_name(transformer, input_features):
    return np.array(["total_defects"])


def make_preprocessor(numeric_cols, categorical_cols, missing_flags=False, total_defects=False):
    """One branch per column type. Everything that learns from data lives in here,
    so cross-validation refits it on every fold and nothing leaks from the validation fold."""
    numeric_branch = make_pipeline(
        SimpleImputer(strategy="median", add_indicator=missing_flags),   # fill gaps with the median
        StandardScaler(),                                                # put numbers on one scale
    )
    categorical_branch = make_pipeline(
        SimpleImputer(strategy="constant", fill_value="missing"),        # a gap becomes its own category
        OneHotEncoder(handle_unknown="infrequent_if_exist",              # rare categories share one column
                      min_frequency=10, sparse_output=False),
    )
    branches = [("num", numeric_branch, numeric_cols),
                ("cat", categorical_branch, categorical_cols)]
    if total_defects:
        defect_cols = [c for c in numeric_cols if "Defects" in c]
        total_branch = make_pipeline(
            FunctionTransformer(_sum_across_columns, feature_names_out=_total_defects_name),
            StandardScaler(),
        )
        branches.append(("total_defects", total_branch, defect_cols))
    return ColumnTransformer(branches, remainder="drop")


def build_pipeline(model, numeric_cols, categorical_cols, **prep_options):
    """Preprocessing and one model, as a single object that cross-validation can refit."""
    return Pipeline([("prep", make_preprocessor(numeric_cols, categorical_cols, **prep_options)),
                     ("model", model)])


def score_model(model, X, y, cv):
    """Cross-validated MAE and R2 (mean and spread over the folds), plus the training MAE."""
    s = cross_validate(model, X, y, cv=cv, return_train_score=True,
                       scoring={"mae": "neg_mean_absolute_error", "r2": "r2"})
    return {
        "MAE (validation)": -s["test_mae"].mean(),
        "MAE spread": s["test_mae"].std(),
        "R2 (validation)": s["test_r2"].mean(),
        "R2 spread": s["test_r2"].std(),
        "MAE (train)": -s["train_mae"].mean(),
    }


def compare_models(models, X, y, cv):
    """Score every model in the dict on the same folds. Returns a table, best first."""
    rows = {name: score_model(m, X, y, cv) for name, m in models.items()}
    return pd.DataFrame(rows).T.round(3).sort_values("MAE (validation)")


# ---- Fold-by-fold helpers (notebook 02, from section 5 on) ----------------
import matplotlib.pyplot as plt


def fold_scores(models, X, y, cv):
    """MAE of every model on every validation fold, as a long table (model, fold, MAE)."""
    rows = []
    for name, model in models.items():
        s = cross_validate(model, X, y, cv=cv, scoring="neg_mean_absolute_error")
        for fold, value in enumerate(-s["test_score"], start=1):
            rows.append({"model": name, "fold": fold, "MAE": value})
    return pd.DataFrame(rows)


def plot_fold_lines(wide, title):
    """One line per validation fold, one point per model. Parallel lines = the fold decides
    how hard the cups are, the model only shifts the line up or down."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for fold, row in wide.iterrows():
        ax.plot(range(len(wide.columns)), row.values, marker="o", label=f"fold {fold}")
    ax.set_xticks(range(len(wide.columns)))
    ax.set_xticklabels(wide.columns, rotation=15, ha="right")
    ax.set_ylabel("MAE (cup points), lower is better")
    ax.set_title(title)
    ax.legend(title="validation fold", loc="upper left", bbox_to_anchor=(1.01, 1))
    plt.tight_layout()
    plt.show()

# ---- Lesson-style curves and scatter (notebooks 02 and 03) --------
from sklearn.model_selection import validation_curve, learning_curve


def plot_predicted_vs_actual(ax, y_true, y_pred, title):
    """Scatter of predicted against actual score with the perfect line (y = x) and a fitted regression line.
    Slope 1 = no shrinking. A flat red line = the model predicts about the average for every lot."""
    low, high = np.quantile(y_true, [0.01, 0.99])
    lo, hi = low - 1, high + 1
    ax.scatter(y_true, y_pred, alpha=0.3, s=12)
    ax.plot([lo, hi], [lo, hi], color="black", linewidth=1, label="perfect (y = x)")
    slope, intercept = np.polyfit(y_true, y_pred, 1)
    ax.plot([lo, hi], [slope * lo + intercept, slope * hi + intercept], color="red", linewidth=2,
            label=f"fitted line (slope {slope:.2f})")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_title(title)
    ax.set_xlabel("actual Total.Cup.Points")
    ax.set_ylabel("predicted Total.Cup.Points")


def _draw_train_vs_validation(ax, x, train_scores, valid_scores, star=True, lower_is_better=False):
    for scores, label, colour in [(train_scores, "train", "C0"), (valid_scores, "validation", "C1")]:
        mean, spread = scores.mean(axis=1), scores.std(axis=1)
        ax.plot(x, mean, marker="o", color=colour, label=label)
        ax.fill_between(x, mean - spread, mean + spread, color=colour, alpha=0.15)
    if star:
        valid_mean = valid_scores.mean(axis=1)
        best = valid_mean.argmin() if lower_is_better else valid_mean.argmax()     # best = lowest MAE, or highest R²
        ax.scatter(x[best], valid_mean[best], marker="*", s=250, color="gold",
                   edgecolor="black", zorder=5, label="best validation")


def _score_label(scoring):
    return {"r2": "R² (higher is better)", "mae": "MAE in cup points (lower is better)"}.get(scoring, scoring)


def plot_validation_curve(ax, model, X, y, cv, param_name, param_range, title, xlabel, log_x=False, scoring="r2"):
    """Train and validation score while ONE setting of the model changes (the lesson plot).
    Both bad = underfitting. Train good but validation getting worse = overfitting. Star = best validation.
    scoring="r2" (default) or "mae" (the average miss in cup points, where lower is better)."""
    param_range = list(param_range)
    use_mae = scoring == "mae"
    train_scores, valid_scores = validation_curve(model, X, y, param_name=param_name, param_range=param_range,
                                                  cv=cv, scoring="neg_mean_absolute_error" if use_mae else scoring,
                                                  n_jobs=-1)
    if use_mae:
        train_scores, valid_scores = -train_scores, -valid_scores     # sklearn reports -MAE; turn it back into MAE
    _draw_train_vs_validation(ax, np.array(param_range), train_scores, valid_scores, lower_is_better=use_mae)
    if log_x:
        ax.set_xscale("log")
    ax.set_xticks(param_range)                                       # show the values we really tried
    ax.set_xticklabels([f"{p:g}" for p in param_range])
    ax.minorticks_off()
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(_score_label(scoring))


def plot_learning_curve(ax, model, X, y, cv, title, random_state, scoring="r2"):
    """Train and validation score as the number of training lots grows. Validation still improving = more data would help.
    scoring="r2" (default) or "mae" (the average miss in cup points, where lower is better)."""
    use_mae = scoring == "mae"
    sizes, train_scores, valid_scores = learning_curve(model, X, y, cv=cv,
                                                       scoring="neg_mean_absolute_error" if use_mae else scoring,
                                                       train_sizes=np.linspace(0.2, 1.0, 6),
                                                       shuffle=True, random_state=random_state, n_jobs=-1)
    if use_mae:
        train_scores, valid_scores = -train_scores, -valid_scores
    _draw_train_vs_validation(ax, sizes, train_scores, valid_scores, star=False, lower_is_better=use_mae)
    ax.set_title(title)
    ax.set_xlabel("number of training lots")
    ax.set_ylabel(_score_label(scoring))


def error_by_group(groups, y_true, y_pred, min_lots=1):
    """How big are the misses inside each group? Lots, MAE and bias (average miss, with its sign).

    Bias below 0 means the model predicts too high for that group (actual - predicted < 0).
    Groups with fewer than min_lots lots are left out, because a handful of lots says too little."""
    miss = y_true - y_pred
    table = pd.DataFrame({"group": groups.astype(object).fillna("missing").values,
                          "miss": miss.values, "abs_miss": miss.abs().values})
    out = table.groupby("group").agg(lots=("miss", "size"), MAE=("abs_miss", "mean"), bias=("miss", "mean"))
    return out[out["lots"] >= min_lots].round(2).sort_values("MAE", ascending=False)
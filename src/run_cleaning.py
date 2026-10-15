"""Clean the CQI data (v2), following the gate 2 decisions.

Why this script exists: cleaning is plain code, not an LLM call. It reads
the decisions Rizki made at gate 2 (references/gate2_decisions.json), runs
the plan in references/cleaning_plan.json and checks every expected count.
If a count is different, it stops instead of adjusting the rule.

Output:
    data/clean/cqi_clean.csv          (never committed)
    references/cleaning_report.json   (one entry per step, plus the checks)

Run from the project root with the Anaconda python:
    /opt/anaconda3/bin/python src/run_cleaning.py
"""

import json
import os
import subprocess
import sys
from datetime import date

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS, PROJECT_ROOT
from functions import (SPECIES, above_to_missing, count_columns,
                       count_per_species, drop_rows_equal, file_fingerprint,
                       kept_columns, load_columns, mask_to_missing,
                       robusta_columns, rows_below, stack_with_sql, step_line,
                       zero_to_missing)

# Why 3: house rule 8, after 3 failures in a row we stop and ask the human.
MAX_ATTEMPTS = 3


def stop(message):
    """Stop the run with one short line for the human (factor 9)."""
    sys.exit(f"Stopped: {message}")


def run_step(name, function, *arguments):
    """Run one step, trying at most MAX_ATTEMPTS times before stopping."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return function(*arguments)
        except Exception as error:
            print(f"{name} attempt {attempt} failed: {error}")
    stop(f"step {name} failed {MAX_ATTEMPTS} times.")


def check(name, real, expected):
    """Compare a real count with the expected one; stop if they differ."""
    if real != expected:
        stop(f"{name}: real {real}, expected {expected}. The rule was not changed.")
    return {"check": name, "real": real, "expected": expected, "result": "pass"}


def find_rule(rules, rule_id):
    """Pick one rule from the decisions file by its id."""
    return next(rule for rule in rules if rule["rule_id"] == rule_id)


# --- Read the gate 2 decisions --------------------------------------------
with open(PATHS["gate2_decisions"]) as file:
    decisions = json.load(file)

moisture_rule = find_rule(decisions["value_rules"], "moisture_zero_to_missing")
high_altitude_rule = find_rule(decisions["value_rules"], "altitude_above_3000_to_missing")
low_altitude_rule = find_rule(decisions["value_rules"], "altitude_below_50_list_only")
total_zero_rule = find_rule(decisions["row_rules"], "drop_total_zero")
# Cleaning v2 rules. Why "limits": the numbers sit in the decisions file as
# plain numbers, so the code never has to cut them out of a sentence.
low_altitude_arabica_rule = find_rule(decisions["value_rules"], "altitude_below_50_arabica_to_missing")
low_moisture_rule = find_rule(decisions["value_rules"], "moisture_low_to_missing")
high_moisture_rule = find_rule(decisions["value_rules"], "moisture_above_014_report_only")
altitude_2500_rule = find_rule(decisions["value_rules"], "altitude_near_2500_report_only")

# Why read the limits from the condition text: the numbers live in one
# place (the decisions file), so code and decisions cannot drift apart.
high_limit = float(high_altitude_rule["condition"].split(">")[1])
low_limit = float(low_altitude_rule["condition"].split("<")[1])

raw_paths = {"arabica": PATHS["raw_cqi_arabica"], "robusta": PATHS["raw_cqi_robusta"]}
steps = []
checks = []

# Why fingerprints first: to prove at the end that the raw files were not changed.
fingerprints_before = {species: file_fingerprint(path) for species, path in raw_paths.items()}

# --- Step 1 and 2: load only the kept columns of each file ----------------
columns_to_load = {"arabica": kept_columns(decisions), "robusta": robusta_columns(decisions)}
tables = {}
for species in SPECIES:
    path = raw_paths[species]
    table = run_step(f"load_{species}", load_columns, path, columns_to_load[species])
    expected_rows = decisions["input_files"][species]["expected_rows"]
    checks.append(check(f"{species} rows loaded", len(table), expected_rows))
    note = "personal data and dropped columns are never loaded"
    if species == "robusta":
        note += "; Acidity, Body and Sweetness not loaded (guessed matches)"
    steps.append(step_line(f"load_{species}", expected_rows, len(table),
                           count_columns(path), table.shape[1], 0, note))
    tables[species] = table

# --- Step 3: stack both tables with the SQL file --------------------------
df = run_step("stack_with_sql", stack_with_sql, tables["arabica"], tables["robusta"],
              PATHS["sql_clean_cqi"])
rows_in = len(tables["arabica"]) + len(tables["robusta"])
checks.append(check("rows after stacking", len(df), rows_in))
robusta_empty = ["Acidity", "Body", "Sweetness"]
steps.append(step_line("stack_with_sql", rows_in, len(df), tables["arabica"].shape[1],
                       df.shape[1], 0,
                       "added species; renamed Fragrance...Aroma to Aroma and Uniform.Cup to "
                       f"Uniformity; {', '.join(robusta_empty)} left empty for "
                       f"{len(tables['robusta'])} robusta rows"))

# Why check the columns now: the output must hold exactly the gate 2 columns.
expected_columns = ["species"] + kept_columns(decisions)
checks.append(check("output columns match gate 2", list(df.columns), expected_columns))

# --- Step 4: Moisture 0.0 becomes missing ---------------------------------
# Why value rules before the row rule: the expected counts were counted on
# the full files, so we apply them to the full table.
rows_before, columns_before = df.shape
df, moisture_counts = zero_to_missing(df, moisture_rule["column"])
checks.append(check("Moisture 0.0 set to missing", moisture_counts, moisture_rule["expected_count"]))
steps.append(step_line(moisture_rule["rule_id"], rows_before, len(df), columns_before,
                       df.shape[1], sum(moisture_counts.values()),
                       f"per species: {moisture_counts}"))

# --- Step 4b (v2): Moisture above 0 and at most 0.05 becomes missing ------
# Why: Moisture is a fraction (0.11 = 11 %); 1 to 5 % is far below normal
# green coffee (about 10 to 12 %), so these values are most likely reporting errors.
moisture_column = low_moisture_rule["column"]
low = low_moisture_rule["limits"]
rows_before, columns_before = df.shape
low_moisture_mask = (df[moisture_column] > low["above"]) & (df[moisture_column] <= low["at_most"])
# Why count the countries before the change: afterwards the values are gone.
low_moisture_countries = (df.loc[low_moisture_mask, "Country.of.Origin"]
                          .value_counts().to_dict())
df, low_moisture_counts = mask_to_missing(df, moisture_column, low_moisture_mask)
checks.append(check(f"Moisture above {low['above']} and at most {low['at_most']} set to missing, arabica",
                    low_moisture_counts["arabica"], low_moisture_rule["expected_count"]["arabica"]))
steps.append(step_line(low_moisture_rule["rule_id"], rows_before, len(df), columns_before,
                       df.shape[1], sum(low_moisture_counts.values()),
                       f"per species: {low_moisture_counts}; no expected Robusta count, reported only"))

# --- Step 4c (v2): report Moisture above 0.14, change nothing ---------------
high_moisture_limit = high_moisture_rule["limits"]["above"]
high_moisture_mask = df[moisture_column] > high_moisture_limit
high_moisture_counts = count_per_species(df, high_moisture_mask)
high_moisture_top10 = (df.loc[high_moisture_mask, ["species", "Country.of.Origin", moisture_column]]
                       .sort_values(moisture_column, ascending=False, kind="stable").head(10))
steps.append(step_line(high_moisture_rule["rule_id"], len(df), len(df), df.shape[1],
                       df.shape[1], 0,
                       f"per species: {high_moisture_counts}; reported only, none changed"))

# --- Step 5: altitude above 3000 m becomes missing ------------------------
rows_before, columns_before = df.shape
df, high_counts = above_to_missing(df, high_altitude_rule["column"], high_limit)
steps.append(step_line(high_altitude_rule["rule_id"], rows_before, len(df), columns_before,
                       df.shape[1], sum(high_counts.values()),
                       f"per species: {high_counts}; no expected count, reported only"))

# --- Step 6: list altitudes under 50 m, change nothing --------------------
low_rows = rows_below(df, low_altitude_rule["column"], low_limit,
                      ["species", "Country.of.Origin", low_altitude_rule["column"]])
steps.append(step_line(low_altitude_rule["rule_id"], len(df), len(df), df.shape[1],
                       df.shape[1], 0, f"{len(low_rows)} rows listed, none changed"))

# --- Step 6b (v2): Arabica altitudes under 50 m become missing --------------
# Why Arabica only: Arabica is not grown at 1 to 13 m, but 40 m (the one
# Robusta row, Ecuador) is possible for Robusta, so that value stays.
altitude_column = low_altitude_arabica_rule["column"]
rule_species = low_altitude_arabica_rule["species"]
below = low_altitude_arabica_rule["limits"]["below"]
rows_before, columns_before = df.shape
low_altitude_mask = (df["species"] == rule_species) & (df[altitude_column] < below)
df, low_altitude_counts = mask_to_missing(df, altitude_column, low_altitude_mask)
checks.append(check(f"{rule_species} altitude under {below} m set to missing",
                    low_altitude_counts, low_altitude_arabica_rule["expected_count"]))
steps.append(step_line(low_altitude_arabica_rule["rule_id"], rows_before, len(df), columns_before,
                       df.shape[1], sum(low_altitude_counts.values()),
                       f"per species: {low_altitude_counts}; the Robusta value (Ecuador, 40 m) is kept"))

# --- Step 6c (v2): list Arabica altitudes near 2500 m, change nothing -------
near = altitude_2500_rule["limits"]
near_2500_mask = ((df["species"] == altitude_2500_rule["species"])
                  & (df[altitude_column] >= near["at_least"])
                  & (df[altitude_column] <= near["at_most"]))
near_2500_rows = (df.loc[near_2500_mask, ["species", "Country.of.Origin", altitude_column]]
                  .sort_values(altitude_column))
steps.append(step_line(altitude_2500_rule["rule_id"], len(df), len(df), df.shape[1],
                       df.shape[1], 0, f"{len(near_2500_rows)} rows listed, none changed"))

# --- Step 7: drop rows where Total.Cup.Points is 0 ------------------------
rows_before, columns_before = df.shape
df, total_zero_counts = drop_rows_equal(df, total_zero_rule["column"], 0)
checks.append(check("rows with Total.Cup.Points 0 dropped",
                    sum(total_zero_counts.values()), total_zero_rule["expected_count"]))
# Why: the decisions say the row is in the Arabica file, so check that too.
expected_file_species = "arabica" if "arabica" in total_zero_rule["expected_file"] else "robusta"
checks.append(check(f"dropped row is in {total_zero_rule['expected_file']}",
                    total_zero_counts[expected_file_species], total_zero_rule["expected_count"]))
steps.append(step_line(total_zero_rule["rule_id"], rows_before, len(df), columns_before,
                       df.shape[1], 0, f"rows dropped per species: {total_zero_counts}"))

# --- Step 8: write the clean table ----------------------------------------
def write_clean_csv(table, path):
    """Write the clean table; index=False because the row numbers are not data."""
    table.to_csv(path, index=False)


os.makedirs(PATHS["clean_data"], exist_ok=True)
run_step("write_clean_csv", write_clean_csv, df, PATHS["clean_cqi"])
steps.append(step_line("write_clean_csv", len(df), len(df), df.shape[1], df.shape[1], 0,
                       "written to the clean data folder (never committed)"))

# --- Final checks ----------------------------------------------------------
species_counts = df["species"].value_counts().reindex(SPECIES, fill_value=0).to_dict()
expected_species = {species: decisions["input_files"][species]["expected_rows"]
                    - total_zero_counts[species] for species in SPECIES}
checks.append(check("rows per species", species_counts, expected_species))

personal_left = [column for column in decisions["drop"]["personal_data"] if column in df.columns]
checks.append(check("personal data columns in output", personal_left, []))
checks.append(check("Moisture 0.0 left", int((df[moisture_rule["column"]] == 0).sum()), 0))
checks.append(check(f"altitude above {high_limit:.0f} m left",
                    int((df[high_altitude_rule["column"]] > high_limit).sum()), 0))

# Cleaning v2 checks: size of the table, and what is left after the new rules.
checks.append(check("rows in the clean table", len(df), sum(expected_species.values())))
checks.append(check("columns in the clean table", df.shape[1], len(expected_columns)))
arabica_moisture = df.loc[df["species"] == "arabica", moisture_column]
checks.append(check("non-empty Moisture values, arabica", int(arabica_moisture.notna().sum()),
                    low_moisture_rule["expected_non_empty_after"]["arabica"]))
checks.append(check(f"Moisture above {low['above']} and at most {low['at_most']} left",
                    int(((df[moisture_column] > low["above"])
                         & (df[moisture_column] <= low["at_most"])).sum()), 0))
checks.append(check(f"arabica altitude under {below} m left",
                    int(((df["species"] == "arabica") & (df[altitude_column] < below)).sum()), 0))

fingerprints_after = {species: file_fingerprint(path) for species, path in raw_paths.items()}
checks.append(check("raw files unchanged", fingerprints_after, fingerprints_before))

# Why git status: data is never committed, so git must not offer anything from data/.
git_data = subprocess.run(["git", "status", "--porcelain", "data/"], cwd=PROJECT_ROOT,
                          capture_output=True, text=True).stdout.strip()
checks.append(check("git status shows nothing from data/", git_data, ""))

# --- Write the report ------------------------------------------------------
report = {
    "dataset_id": decisions["dataset_id"],
    "run_date": date.today().isoformat(),
    "based_on": ["references/gate2_decisions.json", "references/cleaning_plan.json"],
    "steps": steps,
    "rule_counts": [
        {"rule": moisture_rule["rule_id"], "real": moisture_counts,
         "expected": moisture_rule["expected_count"]},
        {"rule": high_altitude_rule["rule_id"], "real": high_counts, "expected": None},
        {"rule": low_altitude_rule["rule_id"], "real": len(low_rows), "expected": None,
         "note": "listed only, no value changed by this rule; the Arabica rows are set to missing by altitude_below_50_arabica_to_missing"},
        {"rule": low_altitude_arabica_rule["rule_id"], "real": low_altitude_counts,
         "expected": low_altitude_arabica_rule["expected_count"]},
        {"rule": low_moisture_rule["rule_id"], "real": low_moisture_counts,
         "expected": low_moisture_rule["expected_count"],
         "countries": low_moisture_countries},
        {"rule": high_moisture_rule["rule_id"], "real": high_moisture_counts, "expected": None,
         "note": "reported only, no value changed"},
        {"rule": altitude_2500_rule["rule_id"], "real": len(near_2500_rows), "expected": None,
         "note": "listed only, no value changed"},
        {"rule": total_zero_rule["rule_id"], "real": total_zero_counts,
         "expected": total_zero_rule["expected_count"],
         "expected_file": total_zero_rule["expected_file"]},
    ],
    "low_altitude_rows": low_rows.to_dict(orient="records"),
    "high_moisture_top10": high_moisture_top10.to_dict(orient="records"),
    "altitude_near_2500_rows": near_2500_rows.to_dict(orient="records"),
    "robusta_empty_columns": {
        "columns": robusta_empty,
        "why": "the Robusta matches for these columns are guesses (medium or weak) at gate 2, so they were left empty instead of guessed",
    },
    "final": {"rows_per_species": species_counts, "columns": df.shape[1],
              "column_names": list(df.columns)},
    "checks": checks,
}
with open(PATHS["cleaning_report"], "w") as file:
    json.dump(report, file, indent=2)
    file.write("\n")

print(f"Done: {len(df)} rows, {df.shape[1]} columns, rows per species {species_counts}.")
print(f"All {len(checks)} checks passed. Report: references/cleaning_report.json")

"""Download one CSV file and write a short profile of it as JSON.

Why this script exists: the Reviewer agent must judge a dataset from facts,
not from memory. This plain code reads the real file and writes those facts
(rows, columns, types, missing values, a few examples, rows per country)
into references/profiles/, where the Reviewer can read them.

It never stores full rows, only counts and at most 3 example values per column.

Run from the project root:
    python src/profile_dataset.py <dataset_id> <direct_csv_url>

Example:
    python src/profile_dataset.py ds_cqi_jldbc_2018 https://raw.githubusercontent.com/.../file.csv
"""

import json
import os
import sys
import urllib.request

import pandas as pd

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS, PROJECT_ROOT

# Why 3: house rule 8, after 3 failures in a row we stop and ask the human.
MAX_ATTEMPTS = 3
EXAMPLES_PER_COLUMN = 3
TOP_COUNTRIES = 15
# Why: columns with these words in the name can hold people's addresses or
# phone numbers. The profile is committed to a public repo, so it keeps
# their counts but never their example values.
PRIVATE_WORDS = ["contact", "address", "phone", "email"]


def download(url, target_path):
    """Download the file, trying at most MAX_ATTEMPTS times."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            urllib.request.urlretrieve(url, target_path)
            return
        except Exception as error:
            # Why one short line: errors should be easy to read (factor 9).
            print(f"Download attempt {attempt} failed: {error}")
    sys.exit(f"Stopped: download failed {MAX_ATTEMPTS} times for {url}")


def profile_column(series):
    """Describe one column: type, missing values, distinct values, examples."""
    # Why dropna first: examples should be real values, not empty cells.
    examples = series.dropna().unique()[:EXAMPLES_PER_COLUMN].tolist()
    is_private = any(word in series.name.lower() for word in PRIVATE_WORDS)
    if is_private:
        examples = ["hidden: may contain personal contact details"]
    return {
        "type": str(series.dtype),
        "missing_count": int(series.isna().sum()),
        "missing_share": round(float(series.isna().mean()), 3),
        "distinct_values": int(series.nunique()),
        # Why tolist above: it turns numpy values into plain Python values for JSON.
        "examples": examples,
    }


def find_country_columns(df):
    """Return the columns whose name contains the word 'country'."""
    # Why the name only: it is a simple rule a human can check by eye.
    # Why skip 'partner': "In-Country Partner" names an organisation, not a country.
    return [col for col in df.columns if "country" in col.lower() and "partner" not in col.lower()]


def profile_countries(series):
    """Count rows per country: the number of countries and the top 15."""
    counts = series.value_counts()
    return {
        "number_of_countries": int(counts.size),
        "rows_without_country": int(series.isna().sum()),
        # Why int(): value_counts gives numpy numbers, JSON needs plain ones.
        "top_15_rows_per_country": {country: int(n) for country, n in counts.head(TOP_COUNTRIES).items()},
    }


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python src/profile_dataset.py <dataset_id> <direct_csv_url>")
    dataset_id = sys.argv[1]
    url = sys.argv[2]

    # Why one folder per dataset: downloaded files stay apart from each other.
    # data/raw/ is gitignored, so the file is never committed.
    raw_folder = os.path.join(PATHS["raw_data"], dataset_id)
    os.makedirs(raw_folder, exist_ok=True)
    file_name = url.split("/")[-1]
    raw_path = os.path.join(raw_folder, file_name)

    download(url, raw_path)

    # Why low_memory=False: pandas then reads each column in one go and
    # gives it one type, instead of guessing per chunk.
    df = pd.read_csv(raw_path, low_memory=False)

    profile = {
        "dataset_id": dataset_id,
        "source_url": url,
        "file_name": file_name,
        "size_bytes": os.path.getsize(raw_path),
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_profiles": {col: profile_column(df[col]) for col in df.columns},
    }

    country_columns = find_country_columns(df)
    if country_columns:
        profile["countries"] = {col: profile_countries(df[col]) for col in country_columns}

    # Why the file name in the profile name: one dataset can have several
    # CSV files, and each one gets its own profile.
    os.makedirs(PATHS["profiles"], exist_ok=True)
    file_stem = os.path.splitext(file_name)[0]
    profile_path = os.path.join(PATHS["profiles"], f"{dataset_id}__{file_stem}.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    # Why one line: the person running it sees the result at a glance.
    n_countries = "no country column"
    if country_columns:
        n_countries = f"{profile['countries'][country_columns[0]]['number_of_countries']} countries"
    print(f"{dataset_id}: {file_name}, {profile['rows']} rows, {profile['columns']} columns, "
          f"{n_countries} -> {os.path.relpath(profile_path, PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

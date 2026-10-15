"""First look at the clean CQI table: diagrams only.

Why this script exists: before any model, we look at the clean data to
see its shape, its gaps and anything odd. Nothing here changes the data,
splits it or fits a model. It only reads the clean table and saves PNGs.

Output (seven PNG files):
    references/figures/first_look/

Run from the project root with the Anaconda python:
    /opt/anaconda3/bin/python src/first_look.py
"""

import os

import matplotlib
# Why "Agg": it draws straight to files, so no window has to open.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Why import from config: the paths are defined once, in src/config.py.
from config import PATHS

# The ten part scores that add up to Total.Cup.Points.
PART_SCORES = ["Aroma", "Flavor", "Aftertaste", "Acidity", "Body",
               "Balance", "Uniformity", "Clean.Cup", "Sweetness", "Cupper.Points"]

# Why bigger fonts: the figures are shown on slides.
plt.rcParams.update({"font.size": 14, "axes.titlesize": 18, "axes.labelsize": 15})

out_dir = PATHS["first_look_figures"]
# Why makedirs: the folder may not exist yet on a fresh clone.
os.makedirs(out_dir, exist_ok=True)


def save(figure, name):
    """Save one figure as PNG and close it, so memory stays free."""
    path = os.path.join(out_dir, name)
    # Why bbox_inches="tight": long country names are not cut off.
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)
    print(f"Saved {name}")


# --- Read the clean table -------------------------------------------------
df = pd.read_csv(PATHS["clean_cqi"])
arabica = df[df["species"] == "arabica"]
print(f"Rows: {len(df)} (arabica {len(arabica)}, robusta {len(df) - len(arabica)})")

# --- a. Rows per country, top 15, split by species --------------------------
# Why crosstab: one row per country, one column per species, cells = row counts.
counts = pd.crosstab(df["Country.of.Origin"], df["species"])
counts["total"] = counts.sum(axis=1)
# Why ascending sort: barh draws the first row at the bottom, so the biggest ends on top.
top15 = counts.sort_values("total").tail(15)

fig, ax = plt.subplots(figsize=(12, 8))
ax.barh(top15.index, top15["arabica"], label="Arabica")
# Why left=: robusta bars start where the arabica bars end (stacked bars).
ax.barh(top15.index, top15["robusta"], left=top15["arabica"], label="Robusta")
ax.set_title("Rows per country (top 15), split by species")
ax.set_xlabel("Number of rows (samples)")
ax.set_ylabel("Country of origin")
# Why set the limit: without it the longest bar touches the right edge.
ax.set_xlim(0, top15["total"].max() * 1.05)
ax.legend()
save(fig, "a_rows_per_country.png")

# --- b. Moisture histogram for Arabica ------------------------------------
# Why dropna: the zeros were set to empty in cleaning, they are not real values.
moisture = arabica["Moisture"].dropna()
# Why these bins: values are rounded to 0.01, so one bin of width 0.01 is
# centred on each value and the small group at 0.01-0.05 shows up on its own.
moisture_bins = np.arange(0.005, moisture.max() + 0.015, 0.01)

fig, ax = plt.subplots(figsize=(12, 7))
ax.hist(moisture, bins=moisture_bins, edgecolor="white")
ax.set_title(f"Arabica moisture (n = {len(moisture)}, empty values left out)")
ax.set_xlabel("Moisture (as stored: 0.11 means 11 %)")
ax.set_ylabel("Number of samples")
save(fig, "b_moisture_arabica.png")

# Why print these groups: to see how many values look too dry, normal or wrong.
print("\nArabica moisture groups (empty values left out):")
print("  0.01 to 0.05 (0.05 included):", ((moisture >= 0.01) & (moisture <= 0.05)).sum())
print("  above 0.05 up to 8:          ", ((moisture > 0.05) & (moisture <= 8)).sum())
print("  above 8 up to 14:            ", ((moisture > 8) & (moisture <= 14)).sum())
print("  above 14:                    ", (moisture > 14).sum())
print("  exactly 0.05:                ", (moisture == 0.05).sum())
# Why both species: the question is about the Moisture column as a whole.
all_moisture = df["Moisture"].dropna()
print(f"Moisture, all rows (n = {len(all_moisture)}): min {all_moisture.min()}, "
      f"median {all_moisture.median()}, max {all_moisture.max()}")
print(f"Moisture, arabica (n = {len(moisture)}): min {moisture.min()}, "
      f"median {moisture.median()}, max {moisture.max()}")

# --- c. Altitude histogram for Arabica ------------------------------------
altitude = arabica["altitude_mean_meters"].dropna()

fig, ax = plt.subplots(figsize=(12, 7))
# Why 100 m bins: fine enough to see the low-altitude rows near 0 m.
ax.hist(altitude, bins=np.arange(0, altitude.max() + 100, 100), edgecolor="white")
ax.set_title(f"Arabica mean altitude (n = {len(altitude)}, empty values left out)")
ax.set_xlabel("Mean altitude (metres)")
ax.set_ylabel("Number of samples")
save(fig, "c_altitude_arabica.png")

# --- d. Total.Cup.Points histogram for Arabica ----------------------------
total = arabica["Total.Cup.Points"]

fig, ax = plt.subplots(figsize=(12, 7))
# Why 0.5-point bins: the scores sit close together (mostly 80 to 85).
ax.hist(total, bins=np.arange(np.floor(total.min()), total.max() + 0.5, 0.5), edgecolor="white")
ax.set_title(f"Arabica Total.Cup.Points (n = {len(total)})")
ax.set_xlabel("Total cup points (out of 100)")
ax.set_ylabel("Number of samples")
save(fig, "d_total_cup_points_arabica.png")

# --- e. Total.Cup.Points box plot, 10 countries with most Arabica rows ----
top10 = arabica["Country.of.Origin"].value_counts().head(10).index
arabica_top10 = arabica[arabica["Country.of.Origin"].isin(top10)]
# Why order by median: higher-scoring countries are easier to compare when sorted.
order = (arabica_top10.groupby("Country.of.Origin")["Total.Cup.Points"]
         .median().sort_values().index)
groups = [arabica_top10.loc[arabica_top10["Country.of.Origin"] == c, "Total.Cup.Points"]
          for c in order]

fig, ax = plt.subplots(figsize=(12, 8))
ax.boxplot(groups, vert=False, tick_labels=order)
ax.set_title("Arabica Total.Cup.Points by country\n(10 countries with the most Arabica rows)")
ax.set_xlabel("Total cup points (out of 100)")
ax.set_ylabel("Country of origin (sorted by median)")
save(fig, "e_total_cup_points_by_country.png")

# --- f. Share of missing values per column --------------------------------
# Why mean of isna: True counts as 1, so the mean is the share of empty cells.
missing = (df.isna().mean() * 100).sort_values()

fig, ax = plt.subplots(figsize=(12, 9))
ax.barh(missing.index, missing.values)
# Why write the numbers: small shares like 0.1 % are too thin to read off the bar.
for position, value in enumerate(missing.values):
    ax.text(value + 0.3, position, f"{value:.1f} %", va="center", fontsize=12)
ax.set_title(f"Share of missing values per column (all {len(df)} rows)")
ax.set_xlabel("Missing values (% of rows)")
ax.set_ylabel("Column")
ax.set_xlim(0, missing.max() + 4)
save(fig, "f_missing_share_per_column.png")

# --- g. Flavour fingerprint: mean part scores per country -----------------
# Same 10 countries as in e; one row per country, one column per part score.
fingerprint = arabica_top10.groupby("Country.of.Origin")[PART_SCORES].mean()
fingerprint = fingerprint.loc[order[::-1]]  # highest median total at the top

fig, ax = plt.subplots(figsize=(14, 8))
# Why viridis: it is matplotlib's default colour map. annot writes each mean in its cell.
sns.heatmap(fingerprint, annot=True, fmt=".2f", cmap="viridis", ax=ax,
            cbar_kws={"label": "Mean score (out of 10)"})
ax.set_title("Flavour fingerprint: mean part scores per country (Arabica)")
ax.set_xlabel("Part score")
ax.set_ylabel("Country of origin")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
save(fig, "g_flavour_fingerprint_heatmap.png")

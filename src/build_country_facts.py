"""Build globe/data/country_facts.json, the one file the globe reads when you hover a country.

Run it from the project-2-ml-rizki folder:
    /opt/anaconda3/bin/python src/build_country_facts.py

Three kinds of input, kept apart in the output so the card can always say where a number came from:
  1. MEASURED   data/clean/cqi_clean.csv                  (your cleaned CQI table)
  2. AGENCIES   data/external/faostat_coffee.csv          (land + total tonnes, FAOSTAT)
                data/external/psd_coffee.csv              (tonnes by type, USDA PSD)
  3. PAPERS     references/literature_cards.json          (composition, fine processing; filled by Scout run 3)
Agency and paper files are optional. A missing file just leaves "no data" on the card.
"""
import json
import os
import re
import sys
import unicodedata
import datetime

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(*parts):
    return os.path.join(ROOT, *parts)


CLEAN = path("data", "clean", "cqi_clean.csv")
FAO_FILE = path("data", "raw", "FAOSTAT_data_en_10-19-2026.csv")
PSD_FILE = path("data", "raw", "psd_coffee.csv")
LIT_FILE = path("references", "literature_cards.approved.json")
OUT = path("globe", "data", "country_facts.json")

MIN_LOTS = 10          # below this many lots a country gets counts only, no mixes or averages
PSD_YEARS_BACK = 1     # PSD's newest year is usually a forecast; use the year before it
PARTS = ["Aroma", "Flavor", "Aftertaste", "Acidity", "Body", "Balance", "Cupper.Points"]

SOURCES = {
    "cqi": {"label": "CQI Q-grader reviews (jldbc copy)",
            "url": "https://github.com/jldbc/coffee-quality-database"},
    "fao": {"label": "FAOSTAT, crops and livestock products (coffee, green)",
            "url": "https://www.fao.org/faostat/en/#data/QCL"},
    "psd": {"label": "USDA FAS, Production, Supply and Distribution (coffee)",
            "url": "https://apps.fas.usda.gov/psdonline/app/index.html#/app/downloads"},
}

# ISO3 -> "Display name | other spellings seen in CQI, FAOSTAT and PSD"
COUNTRIES = {
    "AGO": "Angola", "BOL": "Bolivia|Bolivia (Plurinational State of)", "BRA": "Brazil", "BDI": "Burundi",
    "CMR": "Cameroon", "CAF": "Central African Republic", "CHN": "China|China, mainland|Mainland China",
    "COL": "Colombia", "COD": "DR Congo|Democratic Republic of the Congo|Congo (Kinshasa)|Congo, Democratic Republic of the",
    "COG": "Republic of the Congo|Congo|Congo (Brazzaville)", "CRI": "Costa Rica",
    "CIV": "Côte d'Ivoire|Cote d'Ivoire|Cote d?Ivoire|Ivory Coast", "CUB": "Cuba", "DOM": "Dominican Republic",
    "ECU": "Ecuador", "SLV": "El Salvador", "GNQ": "Equatorial Guinea", "ETH": "Ethiopia", "FJI": "Fiji",
    "GAB": "Gabon", "GHA": "Ghana", "GTM": "Guatemala", "GIN": "Guinea", "GUY": "Guyana", "HTI": "Haiti",
    "HND": "Honduras", "IND": "India", "IDN": "Indonesia", "JAM": "Jamaica", "JPN": "Japan", "KEN": "Kenya",
    "LAO": "Laos|Lao People's Democratic Republic", "LBR": "Liberia", "MDG": "Madagascar", "MWI": "Malawi",
    "MYS": "Malaysia", "MUS": "Mauritius", "MEX": "Mexico", "MMR": "Myanmar|Burma", "NPL": "Nepal",
    "NIC": "Nicaragua", "NGA": "Nigeria", "PAN": "Panama", "PNG": "Papua New Guinea", "PRY": "Paraguay",
    "PER": "Peru", "PHL": "Philippines", "PRI": "Puerto Rico|United States (Puerto Rico)", "RWA": "Rwanda", "SLE": "Sierra Leone",    "LKA": "Sri Lanka", "TWN": "Taiwan|Taiwan, Province of China|China, Taiwan Province of",
    "TZA": "Tanzania|Tanzania, United Republic Of|United Republic of Tanzania", "THA": "Thailand",
    "TLS": "Timor-Leste|East Timor", "TGO": "Togo", "UGA": "Uganda",
    "USA": "United States|United States (Hawaii)|United States of America|USA",
    "VEN": "Venezuela|Venezuela (Bolivarian Republic of)", "VNM": "Vietnam|Viet Nam", "VUT": "Vanuatu",
    "YEM": "Yemen", "ZMB": "Zambia", "ZWE": "Zimbabwe",
    "BLZ": "Belize", "BEN": "Benin", "CPV": "Cabo Verde|Cape Verde", "KHM": "Cambodia", "COM": "Comoros",
    "COK": "Cook Islands", "DMA": "Dominica", "PYF": "French Polynesia", "MOZ": "Mozambique",
    "NCL": "New Caledonia", "VCT": "Saint Vincent and the Grenadines", "WSM": "Samoa",
    "STP": "Sao Tome and Principe", "SAU": "Saudi Arabia", "SUR": "Suriname", "TON": "Tonga",
    "TTO": "Trinidad and Tobago",
}


def norm(name):
    s = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", s.lower())


ALIAS = {}
DISPLAY = {}
for iso, spec in COUNTRIES.items():
    names = spec.split("|")
    DISPLAY[iso] = names[0]
    for n in names:
        ALIAS[norm(n)] = iso


# ---------- the terminal look (rail, diamonds) ----------
DIM, RED, RESET = "\033[2m", "\033[31m", "\033[0m"
problems = []


def say_open(title):
    print(f"┌  {title}")


def say_step(label, summary, ok=True, fix=""):
    print("│")
    if ok:
        print(f"◇  {label}  {DIM}{summary}{RESET}")
    else:
        problems.append(label)
        print(f"◆  {label}")
        print(f"│  {RED}{summary}{RESET}")
        if fix:
            print(f"│  {fix}")


def say_close(text):
    print("│")
    print(f"└  {text}")


# ---------- small helpers ----------
def pick(df, *names):
    low = {str(c).lower().strip(): c for c in df.columns}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    raise KeyError(f"none of {names} in columns {list(df.columns)[:12]}")


def top_counts(series, keep=6):
    counts = series.dropna().astype(str).value_counts()
    top = [[k, int(v)] for k, v in counts.head(keep).items()]
    rest = int(counts.iloc[keep:].sum())
    return top, rest


# ---------- 1. MEASURED: the cleaned CQI table ----------
def build_measured():
    df = pd.read_csv(CLEAN)
    df["iso"] = df["Country.of.Origin"].map(lambda v: ALIAS.get(norm(v)) if pd.notna(v) else None)
    unmatched = sorted(df.loc[df["iso"].isna() & df["Country.of.Origin"].notna(), "Country.of.Origin"].unique())
    arabica = df[df["species"] == "arabica"]
    means = {c: round(float(arabica[c].mean()), 3) for c in PARTS}
    out = {}
    for iso, g in df.dropna(subset=["iso"]).groupby("iso"):
        ga = g[g["species"] == "arabica"]
        block = {"n_lots": int(len(g)), "n_arabica": int(len(ga)), "n_robusta": int((g["species"] == "robusta").sum())}

        alt = g["altitude_mean_meters"].dropna()
        if len(alt) >= MIN_LOTS:
            q = np.percentile(alt, [10, 50, 90])
            block["altitude"] = {"n": int(len(alt)), "min": round(float(alt.min())), "p10": round(float(q[0])),
                                 "median": round(float(q[1])), "p90": round(float(q[2])), "max": round(float(alt.max()))}
        else:
            block["altitude"] = {"n": int(len(alt)), "not_enough": True}

        for key, col in (("varieties", "Variety"), ("processing", "Processing.Method")):
            s = g[col].dropna()
            if len(s) >= MIN_LOTS:
                top, rest = top_counts(s)
                block[key] = {"n": int(len(s)), "top": top, "rest": rest, "missing": int(len(g) - len(s))}
            else:
                block[key] = {"n": int(len(s)), "not_enough": True}

        if len(ga) >= MIN_LOTS:
            block["cup"] = {"n": int(len(ga)), "delta": {c: round(float(ga[c].mean()) - means[c], 2) for c in PARTS}}
        else:
            block["cup"] = {"n": int(len(ga)), "not_enough": True}
        out[iso] = block
    return out, means, unmatched, len(df)


# ---------- 2. AGENCIES ----------
def unit_factor(unit):
    u = str(unit).lower()
    mult = 1000 if "1000" in u else 1
    return mult, u


def load_fao():
    df = pd.read_csv(FAO_FILE, low_memory=False)
    c_area, c_item, c_el = pick(df, "Area"), pick(df, "Item"), pick(df, "Element")
    c_year, c_val, c_unit = pick(df, "Year"), pick(df, "Value"), pick(df, "Unit")
    c_flag = next((c for c in df.columns if str(c).lower().startswith("flag") and "description" not in str(c).lower()), None)
    df = df[df[c_item].astype(str).str.contains("coffee", case=False, na=False)]
    green = df[df[c_item].astype(str).str.contains("green", case=False, na=False)]
    df = green if len(green) else df
    df = df[df[c_area].astype(str) != "China"]          # FAOSTAT's "China" adds in Hong Kong, Macao and Taiwan
    df = df[df[c_val].notna() & (df[c_val] > 0)]          # a 0 here means "not reported", not "no land"
    df = df.assign(iso=df[c_area].map(lambda v: ALIAS.get(norm(v))))
    recent = df[df[c_year] >= df[c_year].max() - 10]
    unmatched = sorted(recent.loc[recent["iso"].isna(), c_area].astype(str).unique())
    df = df.dropna(subset=["iso"])
    out = {}
    for (iso, element), g in df.groupby(["iso", df[c_el].astype(str).str.lower()]):
        g = g.sort_values(c_year)
        row = g.iloc[-1]
        mult, u = unit_factor(row[c_unit])
        if element.startswith("area harvested"):
            kind = "land_ha"
        elif element.startswith("production"):
            kind = "total_t"
        else:
            continue
        if kind == "land_ha" and "ha" not in u:
            raise ValueError(f"FAOSTAT area unit not understood: {row[c_unit]!r}")
        if kind == "total_t" and not (u.strip() in ("t", "1000 t", "tonnes", "tonne") or "t" == u.split()[-1]):
            raise ValueError(f"FAOSTAT production unit not understood: {row[c_unit]!r}")
        out.setdefault(iso, {})[kind] = {"value": round(float(row[c_val]) * mult), "year": int(row[c_year]),
                                         "flag": str(row[c_flag]) if c_flag and pd.notna(row[c_flag]) else None}
    return out, unmatched, int(df[c_year].max())


def load_psd():
    df = pd.read_csv(PSD_FILE, low_memory=False)
    c_country, c_year = pick(df, "Country_Name", "Country"), pick(df, "Market_Year", "Year")
    c_attr, c_unit, c_val = pick(df, "Attribute_Description", "Attribute"), pick(df, "Unit_Description", "Unit"), pick(df, "Value")
    c_comm = next((c for c in df.columns if str(c).lower() == "commodity_description"), None)
    if c_comm:
        df = df[df[c_comm].astype(str).str.contains("coffee", case=False, na=False)]
    year = int(df[c_year].max()) - PSD_YEARS_BACK
    df = df[(df[c_year] == year) & (df[c_val] > 0)]      # 0 means "not reported" in PSD, not "none grown"    
    wanted = {"area harvested": "land_ha", "arabica production": "arabica_t", "robusta production": "robusta_t",
              "other production": "other_t", "production": "total_t"}
    df = df.assign(kind=df[c_attr].astype(str).str.lower().str.strip().map(wanted)).dropna(subset=["kind"])
    df = df.assign(iso=df[c_country].map(lambda v: ALIAS.get(norm(v))))
    unmatched = sorted(df.loc[df["iso"].isna(), c_country].astype(str).unique())
    out = {}
    for _, r in df.dropna(subset=["iso"]).iterrows():
        mult, u = unit_factor(r[c_unit])
        v = float(r[c_val]) * mult
        if r["kind"] == "land_ha":
            if "ha" not in u:                                # the 1000 multiplier already gives hectares
                raise ValueError(f"PSD area unit not understood: {r[c_unit]!r}")
        else:
            if "60" not in u:
                raise ValueError(f"PSD production unit not understood: {r[c_unit]!r}")
            v = v * 60 / 1000                                # 60-kg bags to tonnes
        if v <= 0:
            continue                                         # 0 means "not reported" in PSD, not "none grown"
        out.setdefault(r["iso"], {})[r["kind"]] = round(v)
    return out, unmatched, year


# ---------- main ----------
def main():
    say_open("Build country facts for the globe")
    if not os.path.exists(CLEAN):
        say_step("Clean table", f"{CLEAN} not found", ok=False, fix="Run src/run_cleaning.py first.")
        say_close("Stopped.")
        sys.exit(1)

    measured, means, unmatched, n_rows = build_measured()
    enough = sum(1 for b in measured.values() if b["n_lots"] >= MIN_LOTS)
    say_step("Measured layer (CQI)", f"{n_rows} lots, {len(measured)} countries matched, {enough} with {MIN_LOTS}+ lots")
    if unmatched:
        say_step("Country names not matched", ", ".join(unmatched), ok=False,
                 fix="Add the spelling to COUNTRIES at the top of this file.")

    countries = {iso: {"name": DISPLAY[iso], "cqi": b} for iso, b in measured.items()}
    sources = {"cqi": SOURCES["cqi"]}

    fao_year = psd_year = None
    if os.path.exists(FAO_FILE):
        try:
            fao, miss, fao_year = load_fao()
            for iso, rec in fao.items():
                c = countries.setdefault(iso, {"name": DISPLAY[iso]})
                c["land"] = {"ha": rec["land_ha"]["value"], "year": rec["land_ha"]["year"], "src": "fao"} if "land_ha" in rec else None
                c["total"] = {"t": rec["total_t"]["value"], "year": rec["total_t"]["year"], "src": "fao"} if "total_t" in rec else None
            sources["fao"] = SOURCES["fao"]
            say_step("FAOSTAT", f"{len(fao)} countries, newest year in file {fao_year}")
            if miss:
                say_step("FAOSTAT names not matched", ", ".join(miss), ok=False, fix="Add the spelling to COUNTRIES.")
        except Exception as e:
            say_step("FAOSTAT", f"{type(e).__name__}: {e}", ok=False)
    else:
        say_step("FAOSTAT", "file not found, land and total tonnes stay empty", ok=False,
                 fix="Download 'Crops and livestock products', item Coffee green, elements Area harvested + Production, "
                     "as CSV and save it as data/external/faostat_coffee.csv")

    if os.path.exists(PSD_FILE):
        try:
            psd, miss, psd_year = load_psd()
            for iso, rec in psd.items():
                c = countries.setdefault(iso, {"name": DISPLAY[iso]})
                types = {k: rec[k] for k in ("arabica_t", "robusta_t", "other_t") if k in rec}
                if types or "total_t" in rec:
                    c["by_type"] = {**types, "total_t": rec.get("total_t"), "market_year": psd_year, "src": "psd"}
                if rec.get("land_ha") and not c.get("land"):
                    c["land"] = {"ha": rec["land_ha"], "year": psd_year, "src": "psd"}
            sources["psd"] = SOURCES["psd"]
            say_step("USDA PSD", f"{len(psd)} countries, market year {psd_year}/{str(psd_year + 1)[-2:]}")
            if miss:
                say_step("PSD names not matched", ", ".join(miss), ok=False, fix="Add the spelling to COUNTRIES.")
        except Exception as e:
            say_step("USDA PSD", f"{type(e).__name__}: {e}", ok=False)
    else:
        say_step("USDA PSD", "file not found, tonnes by type stay empty", ok=False,
                 fix="Download the coffee file from PSD Online (bulk data, coffee) and save it as data/external/psd_coffee.csv")

    if os.path.exists(LIT_FILE):
        lit = json.load(open(LIT_FILE, encoding="utf-8"))
        n = 0
        for iso, card in lit.get("countries", {}).items():
            if iso not in DISPLAY:
                say_step("Literature card", f"unknown country code {iso}", ok=False)
                continue
            countries.setdefault(iso, {"name": DISPLAY[iso]})["literature"] = card
            n += 1
        for sid, s in lit.get("sources", {}).items():
            sources[sid] = s
        say_step("Literature cards", f"{n} countries, {len(lit.get('sources', {}))} sources")
    else:
        say_step("Literature cards", "references/literature_cards.approved.json not found, composition stays empty", ok=False,
                 fix="After the Reviewer and you approve literature_cards.json, copy it to literature_cards.approved.json")
        
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"built": datetime.date.today().isoformat(), "min_lots": MIN_LOTS, "cqi_means": means,
                   "sources": sources, "countries": countries}, f, ensure_ascii=False, indent=1)
    say_close(f"Wrote {os.path.relpath(OUT, ROOT)} with {len(countries)} countries."
              + (f"  {len(problems)} step(s) still need attention (◆ above)." if problems else ""))


if __name__ == "__main__":
    main()
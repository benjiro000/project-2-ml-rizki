# Data findings log

A running log of what we know about our data, for the presentation and the README. Collected from references/scout_run_01.json, references/scout_run_02.json, references/reviews/ds_cqi_jldbc_2018.json, the four profiles in references/profiles/ and references/gate2_columns.md. Last updated 16 Oct 2026.

**How each number was found.** Every number below carries one of three tags:

- **[code]**: counted in code from the local copies of the files (src/profile_dataset.py, the read-only counts behind the gate 2 sheet, or the read-only check before the first cleaning run on 16 Oct 2026). This is the strongest evidence.
- **[page summary]**: read from an automatic summary of a web page (Scout runs). The page itself was not read word for word, so treat these as likely but not certain.
- **[search only]**: only seen in a search result. Not confirmed.

Anything marked **uncertain** is a guess or an open question, not a fact.

## 1. Dataset choice

**Chosen dataset:** the Coffee Quality Institute (CQI) reviews scraped by GitHub user jldbc, `ds_cqi_jldbc_2018` (https://github.com/jldbc/coffee-quality-database). We use the two cleaned files: `arabica_data_cleaned.csv` and `robusta_data_cleaned.csv`.

- Size: **1,311 Arabica rows + 28 Robusta rows** (1,339 together), 44 columns each [code]. The raw files have 1,312 Arabica rows (53 columns) and 28 Robusta rows (51 columns) [code]. Which Arabica row is missing from the cleaned file is **unknown**.
- The README says "reviews of 1312 arabica and 28 robusta coffee beans" and "Digitizing 1,340 coffee reviews" [page summary].
- Source: CQI review pages, scraped in January 2018 with Selenium and Beautiful Soup, as stated in the README [page summary].
- Licence: "MIT license" [page summary]. The ledger records it as summary_only.

**Why this dataset:**

- It is about green (unroasted) coffee: Moisture, Category.One.Defects, Category.Two.Defects, Color, Variety, Processing.Method, altitude and country sit next to the cupping scores (Reviewer, from the profiles) [code].
- It has a country on almost every row (36 countries in Arabica, 1 row without a country) [code], which is what the globe needs.
- It has a clear number to predict: Total.Cup.Points, with no empty cells [code].
- Its licence is known, and it is the original scraper repository that the Kaggle and R-package copies point back to [page summary].
- No other candidate was better (see section 4): the image set has no known licence, the sensor dataset has no quality values and an unknown row count, and the May 2023 CQI update could not be opened.

**Size against the brief.** The course brief asks for "at least a few thousand rows" and says to clear an own dataset with the teacher. Our working threshold was 3,000 rows (Scout and Reviewer). With 1,311 Arabica rows used for modelling, the dataset is below that. **Rizki decided to go ahead with this dataset and not to ask the teacher.**

## 2. Data quality findings

### Size and coverage

| Finding | Number | How found |
|---|---|---|
| Arabica cleaned file | 1,311 rows, 44 columns, 649,689 bytes | [code] profile |
| Robusta cleaned file | 28 rows, 44 columns, 13,921 bytes | [code] profile |
| Arabica raw file | 1,312 rows, 53 columns | [code] profile |
| Robusta raw file | 28 rows, 51 columns | [code] profile |
| Arabica countries | 36, plus 1 row without a country | [code] profile |
| Arabica rows per country (top 15) | Mexico 236, Colombia 183, Guatemala 181, Brazil 132, Taiwan 75, United States (Hawaii) 73, Honduras 53, Costa Rica 51, Ethiopia 44, Tanzania, United Republic Of 40, Thailand 32, Uganda 26, Nicaragua 26, Kenya 25, El Salvador 21 | [code] profile |
| Arabica rows in the other 21 countries | 112 together (1,310 with a country minus 1,198 in the top 15); which of them have under 10 rows is **unknown** | [code] Reviewer, by subtraction |
| Robusta countries | 5: India 13, Uganda 10, United States 2, Ecuador 2, Vietnam 1; all 5 also appear in Arabica | [code] profile |

### Values that look wrong or mean "not measured"

| Finding | Number | How found |
|---|---|---|
| Moisture = 0.0, Arabica | 252 of 1,311 rows (19%) | [code] gate 2 sheet, checked again 16 Oct |
| Moisture = 0.0, Robusta | 12 of 28 rows (43%) | [code] gate 2 sheet, checked again 16 Oct |
| Moisture between 0.01 and 0.05, Arabica | 38 rows; also doubtful, most values sit between 0.10 and 0.12. **Not changed** by any rule yet | [code] gate 2 sheet, checked again 16 Oct |
| altitude_mean_meters empty | Arabica 227 rows (17.3%), Robusta 3 rows | [code] |
| altitude_mean_meters above 3,000 m, Arabica | 14 rows (Guatemala 5, Myanmar 5, Brazil, Colombia, Nicaragua, Indonesia 1 each); largest 190,164 m, also 110,000 m and 11,000 m | [code] gate 2 sheet, checked again 16 Oct |
| altitude_mean_meters above 3,000 m, Robusta | 2 rows, both India (3,170 m and 3,140 m) | [code] 16 Oct |
| altitude_mean_meters under 50 m, Arabica | 17 rows: Brazil 13, Costa Rica 2, Kenya 1, Mexico 1 (values 1, 12 and 13 m) | [code] 16 Oct |
| altitude_mean_meters under 50 m, Robusta | 1 row: Ecuador, 40 m | [code] 16 Oct |
| altitude_mean_meters exactly 1 m | 12 Arabica rows | [code] gate 2 sheet |
| Where the low altitudes come from | the typed Altitude text is "1.2" (read as 12 m), "1.3" (13 m), "12oo" (12 m), "1" and "-1" (1 m). **Uncertain:** "1.2" may have meant 1,200 m and "12oo" 1,200 m, but the files do not say | [code] 16 Oct; the meaning is a guess |
| Total.Cup.Points = 0.0 | 1 row, in arabica_data_cleaned.csv (Honduras); every part score on that row is 0.0. Looks like an empty score sheet | [code] gate 2 sheet, checked again 16 Oct |
| Number.of.Bags = 0 | 1 row | [code] gate 2 sheet |
| ICO.Number only zeros ("0", "00", ...) | 67 rows | [code] gate 2 sheet |
| Variety = "Other" | 108 Arabica rows | [code] gate 2 sheet |
| Processing.Method = "Other" | 26 Arabica rows | [code] gate 2 sheet |
| Harvest.Year | text such as "TEST", "mmm", "Mayo a Julio", "4T/10" next to real years in Arabica; 6 clean whole-number years in Robusta | [code] gate 2 sheet |

### Missing values and categories

| Finding | Number | How found |
|---|---|---|
| Arabica Lot.Number empty | 79.4% | [code] profile |
| Arabica Color empty | 20.4% (267 rows); values Green 850, Bluish-Green 112, Blue-Green 82 | [code] profile, counts 16 Oct |
| Arabica Variety empty | 15.3%; 29 distinct values | [code] profile |
| Arabica Processing.Method empty | 11.6% (152 rows); values Washed / Wet 812, Natural / Dry 251, Semi-washed / Semi-pulped 56, Other 26, Pulped natural / honey 14 | [code] profile, counts 16 Oct |
| Robusta Variety empty | 89.3%; only "Other" and "Arusha" | [code] profile |
| Robusta Processing.Method empty | 64.3% (18 rows); Natural / Dry 7, Washed / Wet 3 | [code] profile, counts 16 Oct |
| Robusta ICO.Number / Lot.Number empty | 39.3% / 78.6% | [code] profile |
| Quakers | 1 empty Arabica row; always 0 in Robusta | [code] profile |
| Category.One.Defects maximum | Robusta 63, Arabica 31 | [code] gate 2 sheet |
| Region | 343 distinct spellings in 1,311 Arabica rows | [code] profile |
| Raw files | empty columns (view_certificate_1, view_certificate_2, NA.2, NA.3 and others at 100% empty; Notes 99.6% empty) and numbers stored as text ("12 %", "Sample  90.58") | [code] profile |

### Leakage and comparability

- The ten part scores add up to Total.Cup.Points: the first row's parts add up to 90.59 against a total of 90.58 (Reviewer, from the profile examples) [code]. A model that sees them would just learn the sum.
- Robusta names five part scores differently (Fragrance...Aroma, Uniform.Cup, Salt...Acid, Mouthfeel, Bitter...Sweet). The matches with the Arabica names are guesses from the names and values, not from documentation: two strong, two medium, one weak [code, matching is a guess].
- **Uncertain:** because Robusta's total is the sum of a partly different set of part scores, Arabica and Robusta totals may not be directly comparable.
- **Uncertain:** Owner.1 looks like Owner with original capitals in about 99% of rows (a guess in the gate 2 sheet).
- Country names such as "United States (Hawaii)" and "Tanzania, United Republic Of" will need mapping to the names the globe uses [code].
- No fermentation or luwak value appears in Processing.Method [code].

## 3. Decisions

Decided by Rizki on 16 Oct 2026. Full details and expected counts are in references/gate2_decisions.json; the column sheet references/gate2_columns.md has the "Your decision" column filled in.

1. **Dataset:** CQI 2018 (ds_cqi_jldbc_2018), the two cleaned files, even though it is below a few thousand rows. The teacher is not asked.
2. **Target:** Total.Cup.Points (regression).
3. **Features (8):** Country.of.Origin, Variety, Processing.Method, Color, Moisture, Category.One.Defects, Category.Two.Defects, altitude_mean_meters. Quakers was proposed as a feature but is **dropped**.
4. **Profile columns (10):** Aroma, Flavor, Aftertaste, Acidity, Body, Balance, Uniformity, Clean.Cup, Sweetness, Cupper.Points. Kept in the clean table, never used as features when predicting the total.
5. **Dropped:** everything else, including all eight personal data columns, the three identifiers, Region, Harvest.Year, In.Country.Partner and Quakers.
6. **New column species** ("arabica" or "robusta"). For Robusta, only the strong column matches are used (Fragrance...Aroma as Aroma, Uniform.Cup as Uniformity); the guessed matches (Acidity, Body, Sweetness) stay empty for Robusta rows.
7. **Value rules:** Moisture = 0.0 becomes missing (expected 252 Arabica, 12 Robusta). altitude_mean_meters above 3,000 becomes missing (count reported). Altitude under 50 m is not changed, only listed with its country.
8. **Row rule:** drop rows where Total.Cup.Points is 0 (expected 1, in arabica_data_cleaned.csv).
9. **Scope:** models use Arabica only. Robusta stays in the clean table for the globe and for exploration.

## 4. Not found

- **No row-level Liberica or Excelsa dataset.** Scout run 2 found these species only in paper tables (Herawati et al. 2022 on Excelsa; Mubarak et al. 2019 on Liberica against Arabica) and in theses with restricted full text [page summary].
- **No luwak (civet) or fermentation dataset about the bean itself.** Only papers on civet coffee spectra, a fermentation microbiome dataset (Colombia) and silverskin spectra were seen [search only / page summary].
- **CQI May 2023 update: row count unconfirmed.** The only figure is "1,509 cupping records" from a citing paper [search only]. The Kaggle page returned only its title, and the Baselight mirror is gone (Baselight announced on 7 July 2026 that it has shut down) [page summary]. A search summary says the Baselight listing mentioned data from January 2018, which would mean an overlap with our rows [search only, **uncertain**].
- **Other candidates seen but not used:**
  - USK-Coffee images: 8,000 photos of green Arabica beans, 2,000 per class (peaberry, longberry, premium, defect); no licence stated, only "open for everyone" [page summary].
  - Mendeley AS7265X reflectance dataset: green Arabica and Robusta from four Indonesian origins, CC BY 4.0, row count unknown, sensor readings only [page summary].
  - Zenodo record with NMR spectra of 715 green coffee samples [search only]; the page could not be opened.

## 5. Open items

- **Mendeley file lists:** the landing pages of the MIR defect spectra (dtd2fggpyp), the AS7265X reflectance data (bgpd7mnnjn) and the Java NIRS data (zg89423tkb) showed no file list, sample count or column names [page summary].
- **Roboflow image set** (universe.roboflow.com/packer/coffee-bean-tm9bq): a search summary mentioned Arabica, Excelsa, Liberica and Robusta classes [search only], but the page returned HTTP 403, so classes, licence and whether the beans are green are **unknown**.
- **Herawati et al. 2022** (Excelsa, PMC9410941): Table 1, supplementary Table 1S and Table 3 are known only from a page summary; not read in full, and the supplementary file was not downloaded.
- **Mubarak et al. 2019** (Liberica against Arabica, Asian Journal of Agriculture and Biology): the full-text PDF was not opened, so table numbers and sample counts are **unknown**.
- Not yet decided: what to do with the 38 Arabica Moisture values between 0.01 and 0.05, and with the 18 altitudes under 50 m.
- Which Arabica row is in the raw file but not in the cleaned file is **unknown**.

# Coffee ML: predicting the cup score of a green coffee

Ironhack Data Science & Machine Learning, Project 2. By Rizki F.

**In one line:** from eight facts known before a green coffee is cupped (country, variety, processing method, altitude, moisture, colour and two defect counts), the model predicts the lot's `Total.Cup.Points`. It misses by 1.60 cup points on lots it has never seen, against 1.83 for always guessing the average (about 12 % better). That is good enough to decide which lots to cup first, not to reject lots.

| | |
|---|---|
| The report | [notebooks/03_evaluation_and_interpretation.ipynb](notebooks/03_evaluation_and_interpretation.ipynb) |
| Slides | opening deck in [presentation/](presentation/) (PowerPoint and PDF), then the app slides in [docs/slides.pdf](docs/slides.pdf) |
| Live demo | `streamlit run app.py` (see "Run the demo") |

## The question

A buyer, for example a café like UNTU' Cuisines & Coffee in Amsterdam, has more green-coffee lots than time to cup. Can the facts known before cupping tell which lots to taste first?

- **Target:** `Total.Cup.Points`, a number, so this is a regression (there is no positive class).
- **User and decision:** a buyer deciding which lots to cup first.
- **Metric:** MAE, the average miss in cup points, with R² next to it. MAE is easy to explain ("on average we are 1.6 points off") and is not dominated by a few extreme scores.
- **Which mistake costs more:** specialty coffee starts at about 80 points and most scores sit between 82 and 84, so a miss of 1 to 2 points can move a lot across that line.

## The data and its licence

- Coffee Quality Institute (CQI) green-coffee reviews, scraped in January 2018 by GitHub user jldbc: [coffee-quality-database](https://github.com/jldbc/coffee-quality-database). One row is one lot cupped by a CQI grader.
- 1,311 Arabica and 28 Robusta lots. This project uses Arabica: **1,310 rows after cleaning**.
- **Licence:** the repository is MIT-licensed, but the licence of CQI's underlying data is unclear. Check it before any commercial use. The data is never committed; `download_data.py cqi` fetches it.
- **Traps found and fixed** (plain code in `src/run_cleaning.py`, which stops if a count differs from the plan): numbers stored as text; a moisture of exactly 0.0 in 252 Arabica lots ("not measured" in disguise) and 38 lots between 0.01 and 0.05; altitude above 3,000 m (14 lots) or below 50 m (17 lots), which are typing errors; one lot with a total of 0, dropped.
- **Columns that must go:** the ten part scores (Aroma to Cupper.Points). They add up to the target and exist only after cupping. Also species (one value after filtering) and identifiers.
- **The eight features:** Moisture, altitude, the two defect counts, Country of Origin, Variety, Processing Method, Color.

## Method

- **One split, fixed seed (42):** 1,048 training lots and 262 test lots.
- **No leakage:** everything that learns from data (filling gaps with the median or a "missing" label, scaling, one-hot encoding) sits inside a scikit-learn Pipeline and is fitted on the training lots only.
- **One set of folds:** the baseline and every model are scored on the same 5 cross-validation folds, reported as mean and spread across folds.

## Models compared (training lots, 5-fold cross-validation)

| Model | MAE | Spread | R² |
|---|---|---|---|
| Baseline: always the average | 1.819 | 0.156 | -0.003 |
| Ridge | 1.647 | 0.118 | 0.197 |
| K-nearest neighbours | 1.656 | 0.133 | 0.177 |
| Random forest | 1.628 | 0.127 | 0.206 |
| Gradient boosting | 1.724 | 0.150 | 0.165 |
| Random forest, tuned (best of 48 settings) | 1.597 | | |
| Gradient boosting, tuned | 1.633 | | |
| **Huber regression (final)** | **1.596** | 0.127 | 0.183 |

Two extra features (missing-value flags and total defects) changed nothing beyond the noise, so none were kept. The forest and the boosting model were tuned with a grid search on the training lots. Huber's two settings were checked one at a time, so 1.596 is not a best-of-many number.

**Why Huber.** Ridge and boosting learn by making squared misses small, which pays a lot of attention to the few very bad lots. Huber is a linear model like Ridge, but it uses squared error for small misses and absolute error for big ones, so those lots pull it around less. It beat Ridge on all 5 folds (by 0.05 cup points on average), matched the tuned forest without the 48-setting search, and stays as simple and readable as Ridge. Its R² is lower (0.183 against 0.197) because R² itself measures squared error, while the metric chosen is MAE.

## Final result (262 test lots, scored once)

| | MAE | R² |
|---|---|---|
| Baseline: always the average | 1.830 | -0.001 |
| **Huber (final)** | **1.603** | 0.175 |
| Ridge (first choice, for reference) | 1.605 | 0.224 |

- The test score matches the cross-validated estimate (1.596, spread 0.127).
- 47 % of the test lots are within 1 cup point of the truth, 75 % within 2 and 86 % within 3. The largest miss is 12.5 points.
- **Honesty note:** Ridge was scored on the test set once, before I switched to Huber on the strength of cross-validation alone. The test set was therefore looked at twice. On these 262 lots the two models tie on MAE, so the gain from the cost function is too small to confirm.

## Why there is no threshold

The target is a number, so there is no class threshold to choose. The nearest real decision is the 80-point specialty line. At 80, Huber flags only 1 of the 262 test lots as below 80 (it was right) and catches 1 of the 39 lots that really scored below 80. Raising the cut-off catches more weak lots but flags more good ones: in cross-validation on the training lots, a cut-off of 82 catches 59 % of the sub-80 lots but flags 29 % of all lots, and only 27 % of those flagged are really weak. So the model should rank lots, not screen them. The ranking check: cupping the top fifth by predicted score finds 17 of the 52 truly best test lots (33 %, against about 20 % for a blind pick), and those lots really average 83.5 cup points against 82.1 for all test lots.

## Where it goes wrong

- Lots that really scored below 80 are guessed about 4.5 points too high, and lots of 84 and up about 2.1 points too low. In the middle (80 to 84) the miss is only 0.6 to 1.2.
- It pulls every guess toward the average: on the test lots it predicts only between about 80 and 85.
- Among countries with 10 or more test lots, Honduras (MAE 2.27), Guatemala (2.07) and Hawaii (1.98) are hardest, Colombia easiest (0.99, 45 lots).
- The worst misses are lots that were secretly bad: no altitude on record, or many category-two defects.

## What drives the predictions

Shuffling a column and measuring how much the test error grows: **Country of Origin** (about 0.12 cup points) and **Category Two Defects** (about 0.09) matter most, then Processing Method (about 0.03), with altitude and Variety adding a little. Moisture, Color and Category One Defects barely matter. In coffee terms: where a lot was grown and how many secondary defects the sample has tell the model most. This shows what the model uses, not what causes a high score.

## Limits

- 1,310 Arabica lots from 2018 reviews: nothing about newer harvests or about Robusta.
- Eight columns only. No harvest year, rainfall, shade or finer location than the country.
- Gaps: moisture is missing in about 23 % of the lots, altitude and colour in about 20 %. The pipeline fills them, so the model cannot tell an average lot from one that was never measured.
- A small test set (262 lots), so the country and score-band results rest on 10 to 45 lots each.
- The target is one person's score for one cup, so part of the miss may be noise no model can remove.

## Run the demo

The demo loads the saved model and predicts for new lots. It needs the cleaned data and `models/final_model.joblib`, so reproduce the project first (next section), then:

```
streamlit run app.py
```

Slide 9 shows the coffee globe from `static/globe/`, a copy of `globe/`. After any change to the globe run `python src/sync_static_globe.py`. The globe loads its map from the internet.

## Reproduce

```
git clone https://github.com/benjiro000/project-2-ml-rizki.git
cd project-2-ml-rizki
pip install -r requirements.txt
python download_data.py cqi          # the two CQI files into data/raw/ds_cqi_jldbc_2018/
python src/run_cleaning.py           # data/clean/cqi_clean.csv and references/cleaning_report.json
```

Then run notebooks 01, 02 and 03 in order (Restart and Run All). Notebook 03 saves `models/final_model.joblib`, which is gitignored. `notebooks/00_sql_setup.ipynb` is an optional SQL look at the raw files.

## Repo layout

```
README.md, RUBRIC.md, requirements.txt, download_data.py
app.py, .streamlit/       the Streamlit presentation and demo
notebooks/                00 SQL setup (optional), 01 EDA and baseline, 02 pipelines and models, 03 evaluation (the report)
src/                      functions.py, config.py (seed and paths), run_cleaning.py, sql/, the globe data builders
data/, models/            contents are gitignored
references/               source ledger (sources.json), cleaning plan and report
presentation/             the opening deck (PowerPoint and a PDF copy)
docs/slides.pdf           the app slides as a PDF
globe/, static/globe/     the coffee globe (and the copy the app serves)
prompts/                  prompts of the small agents that helped build the project
```

## Extra: the coffee globe and the agents

`globe/coffee_globe.html` is an interactive globe of coffee-growing countries, with layers for chain routes and Cup of Excellence, a per-country card and a References panel. Every source used anywhere in the project is recorded in `references/sources.json` (the panel is built from it). Six small agents built with HumanLayer helped with data search, review, cleaning and the globe. People approved each step at three gates (datasets, columns, publishing), and the cleaning and the modelling are plain code, not language-model calls.
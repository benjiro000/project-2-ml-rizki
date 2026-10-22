import inspect
import json
import re
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import HuberRegressor, LinearRegression, LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, f1_score, mean_absolute_error,
                             mean_squared_error, precision_score, r2_score, recall_score,
                             silhouette_samples, silhouette_score)
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeRegressor, plot_tree

try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:          # the 3D diagram shows an install hint instead
    px = go = None

from src.config import PATHS, RANDOM_STATE
from src.functions import (build_pipeline, compare_models, error_by_group, get_feature_columns,
                           load_arabica, make_cv, make_preprocessor, plot_learning_curve,
                           plot_predicted_vs_actual, plot_validation_curve, score_model,
                           split_once)

st.set_page_config(page_title="Coffee ML Presentation by Rizki F.", layout="wide")

# ------------------------------------------------------------------
# PRESENTATION SCREEN
# Designed for a 1920 x 1080 screen (Full HD, 16:9). Every size below is in rem, and the rem
# follows the width of the window (20 px at 1920 wide), so the page keeps the same look on a
# 1280 x 720 projector or a 2560 x 1440 monitor. To make all text bigger or smaller, change
# the 1.0417vw (1920 x 1.0417% = 20 px) in the first rule.
# ------------------------------------------------------------------
PRESENTATION_CSS = """
<style>
html { font-size: clamp(12px, 1.0417vw, 40px) !important; }

/* page area and sidebar */
.block-container, [data-testid="stMainBlockContainer"] {
    padding: 2.4rem 3rem 3rem 3rem !important; max-width: 100% !important; }
[data-testid="stSidebar"][data-collapsed="false"] {
    min-width: 19rem !important; max-width: 19rem !important; width: 19rem !important; }
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] p { font-size: 1rem !important; }

/* text: title, subheader, body, caption */
[data-testid="stHeading"] h1, h1 { font-size: 2.6rem !important; line-height: 1.2 !important; }
[data-testid="stHeading"] h3, h3 { font-size: 1.6rem !important; line-height: 1.3 !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {
    font-size: 1.1rem !important; line-height: 1.55 !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    font-size: 0.95rem !important; line-height: 1.5 !important; }

/* numbers, tabs, dropdowns, code, tables */
[data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] p { font-size: 1rem !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] [data-testid="stMarkdownContainer"] p {
    font-size: 2.3rem !important; }
button[data-baseweb="tab"] p { font-size: 1.1rem !important; }
[data-testid="stExpander"] summary p { font-size: 1rem !important; }
[data-testid="stRadio"] label p, [data-testid="stCheckbox"] label p,
[data-testid="stSelectbox"] label p, [data-testid="stNumberInput"] label p { font-size: 1rem !important; }
code, pre, [data-testid="stCode"] * { font-size: 0.85rem !important; }
[data-baseweb="select"] div, [data-baseweb="input"] input, [data-baseweb="base-input"] input {
    font-size: 1rem !important; }

/* charts: as wide as the page, but never taller than 60% of the window,
   so a square chart is centred and still fits next to its title */
[data-testid="stFullScreenFrame"]:has([data-testid="stImage"]) {
    display: flex !important; justify-content: center !important; }
[data-testid="stImage"] img, [data-testid="stImageContainer"] img {
    max-height: 60vh !important; width: auto !important; max-width: 100% !important;
    object-fit: contain; }
.st-key-tall_plot img { max-height: 66vh !important; }

/* loading sign next to the Stop button: the little running man is hidden and a plain
   spinning circle takes its place (grey, so it works on a light and a dark screen) */
[data-testid="stStatusWidgetRunningIcon"] > *, [data-testid="stStatusWidget"] [aria-label="Running..."] > * {
    display: none !important; }
[data-testid="stStatusWidgetRunningIcon"]::after, [data-testid="stStatusWidget"] [aria-label="Running..."]::after {
    content: ""; box-sizing: border-box; width: 1.1rem; height: 1.1rem; border-radius: 50%;
    border: 0.15rem solid rgba(128, 128, 128, 0.3); border-top-color: rgba(128, 128, 128, 0.95);
    animation: loading-spin 0.8s linear infinite; }
@keyframes loading-spin { to { transform: rotate(360deg); } }
</style>
"""
st.markdown(PRESENTATION_CSS, unsafe_allow_html=True)

# text inside the charts, sized to match the page text
plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12,
                     "xtick.labelsize": 11, "ytick.labelsize": 11, "legend.fontsize": 11})

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "models" / "final_model.joblib"
GLOBE_SOURCES_PATH = ROOT / "globe" / "data" / "sources.json"   # the file the globe's References button reads
GLOBE_URL = "/app/static/globe/coffee_globe.html"
RAW_FOLDER = ROOT / "data" / "raw"
SQL_FOLDER = ROOT / "src" / "sql"
CLEANING_REPORT_PATH = ROOT / "references" / "cleaning_report.json"
TARGET = "Total.Cup.Points"
PART_SCORES = ["Aroma", "Flavor", "Aftertaste", "Acidity", "Body", "Balance", "Cupper.Points"]

PROJECT_TITLE = "From Green Bean to Cup Score"
PRESENTER = "Rizki"
DEMO_TITLE = "Demo: Green Coffee Cup Point Calculator"

# Raw columns whose names contain one of these words are hidden on the Raw datasets tab
# (names, contacts, addresses). They never reach the clean table either.
PERSONAL_WORDS = ["owner", "producer", "contact", "address", "phone", "email"]
MAX_ROWS_SHOWN = 20000

# The title of each raw-data dropdown: the website or company the data came from.
# A raw file gets the name whose key appears in its file name or its source link.
RAW_SOURCE_NAMES = {
    "cqi": "Coffee Quality Institute (CQI), via GitHub",
    "faostat": "FAOSTAT · Food and Agriculture Organization (FAO)",
    "psd": "USDA Foreign Agricultural Service · PSD Online",
}

# The numbers of neighbours tried on the KNN diagrams (the chosen k must be in the list)
KNN_SETTINGS = [1, 3, 5, 10, 15, 25, 40, 60, 100]

# The alphas tried on the Huber diagram (the chosen alpha must be in the list)
HUBER_ALPHAS = [0.01, 0.1, 1, 10, 100, 1000]

# Classification Evaluation: for each model, the setting on the x axis, the values tried,
# the value used in the figures above the diagram, and how to read it.
CLASS_SETTINGS = {
    "K-nearest neighbours": {
        "label": "number of neighbours k (log scale): more neighbours = simpler model",
        "values": KNN_SETTINGS, "chosen": 25, "log": True,
        "explain": ("KNN stamps a lot with the vote of its k most similar lots, and 'similar' means "
                    "close by distance, which is why the numbers are scaled first. At k = 1 every lot "
                    "is its own nearest neighbour, so the train score is close to perfect but the model "
                    "is only memorising. More neighbours make a simpler model."),
    },
    "Logistic regression": {
        "label": "C (log scale): smaller C = held back harder = simpler model",
        "values": [0.001, 0.01, 0.1, 1, 10, 100], "chosen": 1.0, "log": True,
        "explain": ("Logistic regression draws one straight boundary through the scaled features and "
                    "turns the result into a probability: a lot above 50% is stamped '80 or more'. "
                    "C sets how freely it may bend to the training lots. A small C holds it back "
                    "(simpler), a large C lets it follow the training lots closely."),
    },
}

# The model comparison table from notebook 02 (MAE in cup points, lower is better).
# The Huber row comes from the cost-function test in section 6 (same folds).
# If you re-ran notebook 02 after the latest cleaning, retype the numbers here.
COMPARISON = pd.DataFrame(
    {
        "MAE validation": [1.596, 1.628, 1.647, 1.656, 1.724, 1.819],
        "MAE spread":     [0.127, 0.127, 0.118, 0.133, 0.150, 0.156],
        "MAE train":      [1.557, 1.296, 1.596, 1.591, 1.070, 1.817],
    },
    index=["Huber (linear)", "Random forest", "Ridge (linear)", "K-nearest neighbours",
           "Gradient boosting", "Baseline (mean)"],
)

SQL_EXPLAINED = {
    "SELECT": "picks the columns we keep (personal-data columns are never selected)",
    "AS": "renames a column so the Arabica and Robusta files use the same name",
    "UNION ALL": "stacks the Arabica rows and the Robusta rows into one table",
    "JOIN": "matches rows of two tables on a shared key",
    "WHERE": "keeps only the rows that meet a rule",
    "CASE": "sets a value by a rule, for example an impossible value becomes missing",
    "NULLIF": "turns a given value into missing (NULL)",
    "CAST": "changes a column's type, for example text to number",
    "REPLACE": "cleans text, for example removes a % sign",
    "GROUP BY": "groups rows to count or average per group",
    "COUNT": "counts rows",
}


# ------------------------------------------------------------------
# CODE DROPDOWNS
# ------------------------------------------------------------------
def source_of(*functions):
    """The real source code of functions, so what we show is what runs."""
    parts = []
    for function in functions:
        try:
            text = inspect.getsource(function)
        except (OSError, TypeError):
            text = f"# source of {function.__name__} is not available"
        lines = [line for line in text.splitlines() if not line.startswith("@st.")]
        parts.append("\n".join(lines))
    return "\n\n".join(parts)


def code_box(model_blocks, *draw_functions, model_title="1. The model",
             draw_title="2. The code that draws the diagram",
             label="Show the code behind this diagram"):
    """A dropdown under a diagram: first the model (or data), then the drawing code.
    model_blocks is a list of code strings, or a dict {tab name: code} to get one tab each."""
    with st.expander(label):
        st.markdown(f"**{model_title}**")
        if isinstance(model_blocks, dict):
            for tab, (name, code) in zip(st.tabs(list(model_blocks)), model_blocks.items()):
                with tab:
                    st.code(code, language="python", wrap_lines=True)
        else:
            for block in model_blocks:
                st.code(block, language="python", wrap_lines=True)
        if draw_functions:
            st.markdown(f"**{draw_title}**")
            st.code(source_of(*draw_functions), language="python")


def show_plot(fig):
    st.pyplot(fig)
    plt.close(fig)


# ------------------------------------------------------------------
# REFERENCES, RAW DATA AND SQL HELPERS
# ------------------------------------------------------------------
def clean_text(value):
    """Plain text for markdown. A $ is escaped so Streamlit does not read it as maths."""
    return str(value or "").replace("$", "\\$").strip()


def load_sources():
    """The sources the globe's References button shows."""
    if not GLOBE_SOURCES_PATH.exists():
        return []
    raw = json.loads(GLOBE_SOURCES_PATH.read_text())
    return raw.get("sources", []) if isinstance(raw, dict) else raw


def source_line(source):
    """One source as it should read on the References page."""
    title = clean_text(source.get("title")) or clean_text(source.get("source_id"))
    url = source.get("url")
    head = f"**[{title}]({url})**" if url else f"**{title}**"
    author = clean_text(source.get("publisher_or_author"))
    licence = clean_text(source.get("licence"))
    if licence and source.get("licence_url"):
        licence = f"[{licence}]({source['licence_url']})"
    checked = clean_text(source.get("verification")).replace("_", " ")
    used_for = clean_text(source.get("used_for"))

    lines = [head + (f" — {author}" if author else "")]
    details = []
    if licence:
        details.append(f"Licence: {licence}")
    if checked:
        details.append(f"Checked: {checked}")
    if details:
        lines.append(" · ".join(details))
    if used_for:
        lines.append(f"Used for: {used_for}")
    return "  \n".join(lines)


@st.cache_data
def read_raw(path_text):
    return pd.read_csv(path_text, low_memory=False, encoding_errors="replace")


def find_dataset_source(file_name, sources):
    """The ledger entry (type dataset) that best matches a raw file name."""
    words = [w for w in re.split(r"[^a-z0-9]+", file_name.lower())
             if len(w) >= 3 and w not in {"raw", "csv", "data"}]
    best, best_score = None, 0
    for source in sources:
        if source.get("type") != "dataset":
            continue
        text = " ".join(str(source.get(key, "")) for key in ("source_id", "title", "url")).lower()
        score = sum(word in text for word in words)
        if score > best_score:
            best, best_score = source, score
    return best


def friendly_source_name(path, source):
    """A reader-friendly title for a raw file: the website or company the data came from."""
    source = source or {}
    haystack = " ".join([path.name, str(source.get("url", "")), str(source.get("source_id", ""))]).lower()
    name = next((label for word, label in RAW_SOURCE_NAMES.items() if word in haystack), None)
    if name is None:
        name = clean_text(source.get("publisher_or_author")) or path.stem
    kind = next((word.capitalize() for word in ("arabica", "robusta") if word in path.name.lower()), None)
    return f"{name} · {kind}" if kind else name


def sql_files():
    return sorted(SQL_FOLDER.glob("*.sql")) if SQL_FOLDER.exists() else []


def sql_functions_used(files):
    """Which SQL functions really appear in the .sql files (comments ignored)."""
    rows = []
    for word, meaning in SQL_EXPLAINED.items():
        found_in = []
        for path in files:
            text = "\n".join(line for line in path.read_text().splitlines()
                             if not line.strip().startswith("--"))
            if re.search(rf"\b{re.escape(word)}\b", text, flags=re.IGNORECASE):
                found_in.append(path.name)
        if found_in:
            rows.append({"SQL function": word, "What it does here": meaning,
                         "Found in": ", ".join(found_in)})
    return pd.DataFrame(rows)


def find_erd_images():
    found = []
    for folder in [ROOT / "images", ROOT / "references" / "figures"]:
        if folder.exists():
            found += sorted(p for p in folder.glob("erd*")
                            if p.suffix.lower() in {".png", ".jpg", ".jpeg"})
    return found


# ------------------------------------------------------------------
# MODEL AND DATA CODE SHOWN IN THE DROPDOWNS (from notebooks 01, 02 and 03)
# If you changed a setting in a notebook, change it here too.
# ------------------------------------------------------------------
DATA_CALL = 'df = load_arabica(PATHS["clean_data"])   # the clean CQI table, Arabica rows only'

BASELINE_CODE = '''from sklearn.dummy import DummyRegressor
from sklearn.model_selection import cross_val_score

cv = make_cv(RANDOM_STATE)                    # the same 5 folds for every model
baseline = DummyRegressor(strategy="mean")    # always says "about the average score"

mae = -cross_val_score(baseline, X_train, y_train, cv=cv, scoring="neg_mean_absolute_error")
print("Baseline MAE:", mae.mean().round(3), "+/-", mae.std().round(3))'''

FINAL_MODEL_CODE = '''from sklearn.linear_model import HuberRegressor
from src.functions import build_pipeline

# preprocessing + Huber in ONE object, so cross-validation refits everything on every fold
# Huber counts small misses by their square and big misses only by their size, so a few
# very low scores pull the line around less (best_options is set in notebook 02, section 5)
final_model = build_pipeline(HuberRegressor(alpha=10.0, epsilon=1.35, max_iter=1000),
                             numeric_cols, categorical_cols, **best_options)
final_model.fit(X_train, y_train)

# cross-validated score on the training lots, same folds as the baseline
mae = -cross_val_score(final_model, X_train, y_train, cv=cv, scoring="neg_mean_absolute_error")'''

PREDICT_CODE = '''pred_test = final_model.predict(X_test)     # the test lots, scored once
residuals = y_test - pred_test             # actual - predicted, in cup points'''

DEMO_CODE = '''import joblib
import numpy as np
import pandas as pd

final_model = joblib.load("models/final_model.joblib")   # the saved pipeline from notebook 03

# one new coffee = one row, with the same column names the model was trained on
new_row = pd.DataFrame([{
    "Country.of.Origin": country, "Variety": variety, "Processing.Method": process,
    "Moisture": moisture,                      # np.nan if it was not measured
    "Category.One.Defects": defects_one, "Category.Two.Defects": defects_two,
    "Color": color,
    "altitude_mean_meters": altitude,          # np.nan if unknown
}])
prediction = final_model.predict(new_row)[0]   # the pipeline fills gaps and encodes by itself'''

REAL_LOT_CODE = '''lot = X_test.loc[[lot_id]]                 # a lot the model never saw in training
predicted = final_model.predict(lot)[0]
actual = y_test.loc[lot_id]                # what the graders really gave it'''


def pipeline_line(name, estimator):
    return f"{name} = build_pipeline({estimator}, numeric_cols, categorical_cols, **best_options)"


MODEL_CODE = {
    "Baseline": "from sklearn.dummy import DummyRegressor\n\n"
                + pipeline_line("baseline", 'DummyRegressor(strategy="mean")'),
    "Ridge": "from sklearn.linear_model import Ridge\n\n"
             + pipeline_line("ridge", "Ridge(alpha=10.0)"),
    "Huber": "from sklearn.linear_model import HuberRegressor\n\n"
             + pipeline_line("huber", "HuberRegressor(alpha=10.0, epsilon=1.35, max_iter=1000)"),
    "Nearest neighbours": "from sklearn.neighbors import KNeighborsRegressor\n\n"
                          + pipeline_line("knn", "KNeighborsRegressor(n_neighbors=25)"),
    "Random forest": "from sklearn.ensemble import RandomForestRegressor\n\n"
                     + pipeline_line("forest", "RandomForestRegressor(n_estimators=300, min_samples_leaf=5,\n"
                                               "                          random_state=RANDOM_STATE, n_jobs=-1)"),
    "Gradient boosting": "from sklearn.ensemble import HistGradientBoostingRegressor\n\n"
                         + pipeline_line("boosting", "HistGradientBoostingRegressor(random_state=RANDOM_STATE)"),
    "Tuned forest": '''from sklearn.model_selection import GridSearchCV

rf = build_pipeline(RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE),
                    numeric_cols, categorical_cols, **best_options)
rf_grid = {"model__max_depth": [4, 8, 12, None],
           "model__min_samples_leaf": [1, 5, 10, 20],
           "model__max_features": [0.3, 0.6, 1.0]}
search = GridSearchCV(rf, rf_grid, cv=cv, scoring="neg_mean_absolute_error",
                      n_jobs=-1).fit(X_train, y_train)''',
    "How they are scored": source_of(make_cv, score_model, compare_models),
}


def saved_model_text(model):
    return ("# Inside the saved file models/final_model.joblib\n"
            f"# final step: {model.steps[-1][1]}\n"
            f"# columns it expects: {list(model.feature_names_in_)}")


# ------------------------------------------------------------------
# REGRESSION AND CLASSIFICATION EVALUATION HELPERS
# ------------------------------------------------------------------
def make_regressors():
    """The four regression models: the final Huber model and three lesson models. KNN works by
    distance, so the numbers must be on one scale: the StandardScaler inside build_pipeline
    does that for every model."""
    return {
        "Huber regression (final model)": HuberRegressor(alpha=10.0, epsilon=1.35, max_iter=1000),
        "K-nearest neighbours": KNeighborsRegressor(n_neighbors=25),
        "Linear regression": LinearRegression(),
        # a tree with no limits memorises the training lots, so depth and leaf size are capped
        "Decision tree": DecisionTreeRegressor(max_depth=5, min_samples_leaf=10,
                                               random_state=RANDOM_STATE),
    }


def regression_figures(y_true, predicted):
    """The four standard figures for a regression model."""
    mse = mean_squared_error(y_true, predicted)
    return {"RMSE": np.sqrt(mse),
            "MSE": mse,
            "MAE": mean_absolute_error(y_true, predicted),
            "R²": r2_score(y_true, predicted)}


def class_model_at(name, setting, numeric_cols, categorical_cols):
    """A classifier pipeline with one value of its setting. The scaling happens inside the
    pipeline, which KNN needs because it works by distance."""
    if name == "K-nearest neighbours":
        classifier = KNeighborsClassifier(n_neighbors=setting)
    elif name == "Logistic regression":
        classifier = LogisticRegression(C=setting, max_iter=1000)
    else:
        classifier = DummyClassifier(strategy="most_frequent")
    return build_pipeline(classifier, numeric_cols, categorical_cols)


def tree_feature_names(pipe):
    """Readable column names after the pipeline has filled, scaled and encoded everything."""
    try:
        names = pipe.named_steps["prep"].get_feature_names_out()
    except Exception:
        return None
    return [str(name).split("__", 1)[-1] for name in names]


# ------------------------------------------------------------------
# DIAGRAMS (each one returns a figure; the dropdowns show their code)
# ------------------------------------------------------------------
def compact_legend(ax):
    """Short legend words: the dots, the perfect line, the model's own trend."""
    handles, labels = ax.get_legend_handles_labels()
    compact = []
    for handle, label in zip(handles, labels):
        if isinstance(handle, Line2D):
            x, y = handle.get_data()
            if len(x) > 1 and np.allclose(x, y):
                label = "Perfect: predicted = actual"
            elif len(x) > 1 and x[-1] != x[0]:
                label = f"Model trend (slope {(y[-1] - y[0]) / (x[-1] - x[0]):.2f})"
        elif isinstance(handle, PathCollection):
            label = "Lots"
        compact.append(label)
    ax.legend(handles, compact, loc="upper left")


def draw_score_3d(df, x_feature, y_feature, color_by, show_specialty_line=False):
    """3D scatter: two features on the floor, the cup score as the height, one dot per lot.
    The red 80-point plane is only drawn when show_specialty_line=True."""
    columns = list(dict.fromkeys([x_feature, y_feature, TARGET, "Country.of.Origin",
                                  "Variety", "Processing.Method", color_by]))
    data = df[columns].dropna(subset=[x_feature, y_feature]).copy()
    if color_by != TARGET:
        # a legend with 8 groups is readable, so the rarer ones are grouped as "Other"
        labels = data[color_by].fillna("Missing")
        top = labels.value_counts().head(8).index
        data[color_by] = labels.where(labels.isin(top), "Other")
    fig = px.scatter_3d(data, x=x_feature, y=y_feature, z=TARGET, color=color_by,
                        hover_name="Country.of.Origin", hover_data=["Variety", "Processing.Method"],
                        opacity=0.65)
    fig.update_traces(marker={"size": 3})
    if show_specialty_line:
        # a faint red plane at 80 points: the lots above it are specialty coffee
        fig.add_trace(go.Surface(
            x=[data[x_feature].min(), data[x_feature].max()],
            y=[data[y_feature].min(), data[y_feature].max()],
            z=[[80, 80], [80, 80]], opacity=0.25, showscale=False,
            colorscale=[[0, "red"], [1, "red"]], name="80 = specialty line",
            showlegend=True, hoverinfo="skip"))
    # The numbers along the axes are set to 12, which is Streamlit's default size. The feature
    # titles keep the size they had (14), which is written out here so it cannot shrink with them.
    axis_text = {"tickfont": {"size": 12}, "title": {"font": {"size": 14}}}
    fig.update_scenes(xaxis=axis_text, yaxis=axis_text, zaxis=axis_text)
    # more room above and below the diagram (top 40 -> 80, bottom 0 -> 60); the height grew
    # a little too (650 -> 700) so the 3D box itself does not shrink much
    fig.update_layout(height=700, margin={"l": 0, "r": 0, "t": 80, "b": 60},
                      title=f"{len(data)} lots: {x_feature} and {y_feature} against {TARGET}")
    return fig


def draw_score_distribution(df):
    fig, ax = plt.subplots(figsize=(9, 4))
    sns.histplot(df[TARGET], bins=40, kde=True, ax=ax)
    ax.axvline(80, color="red", linestyle="--", label="80 = specialty line")
    ax.legend()
    ax.set_title("Total cup points, Arabica")
    return fig


def draw_score_by_country(df):
    top_countries = df["Country.of.Origin"].value_counts().head(10).index.tolist()
    if "Indonesia" not in top_countries:        # always show Indonesia next to the 10 biggest origins
        top_countries.append("Indonesia")
    sub = df[df["Country.of.Origin"].isin(top_countries)]
    order = sub.groupby("Country.of.Origin")[TARGET].median().sort_values(ascending=False).index
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=sub, x=TARGET, y="Country.of.Origin", order=order, ax=ax)
    ax.set_title("Score by country (top 10 by number of samples, plus Indonesia)")
    return fig


def draw_altitude_moisture(df):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.scatterplot(data=df, x="altitude_mean_meters", y=TARGET, alpha=0.4, ax=axes[0])
    sns.scatterplot(data=df, x="Moisture", y=TARGET, alpha=0.4, ax=axes[1])
    axes[0].set_title("Altitude vs score")
    axes[1].set_title("Moisture vs score")
    return fig


def draw_missing_values(df, features):
    missing = df[features].isna().mean().sort_values() * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(missing.index, missing.values)
    ax.set_xlabel("% of rows empty")
    ax.set_title("Missing values per feature")
    return fig


def draw_knn_curve(table, chosen_k, eval_label):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    panels = [("R²", "R² (higher is better)"),
              ("MAE", "MAE in cup points (lower is better)")]
    for ax, (metric, ylabel) in zip(axes, panels):
        ax.plot(table.index, table[f"train {metric}"], marker="o", label="train")
        ax.plot(table.index, table[f"eval {metric}"], marker="o", label=eval_label)
        ax.axvline(chosen_k, color="grey", linestyle="--", label=f"chosen k = {chosen_k}")
        ax.set_xscale("log")
        ax.set_xlabel("number of neighbours k (log scale): more neighbours = simpler model")
        ax.set_ylabel(ylabel)
        ax.legend()
    axes[0].set_title("R² against k")
    axes[1].set_title("MAE against k")
    fig.tight_layout()
    return fig


def draw_huber_fit(y_eval, pred_eval, eval_label):
    """Predicted against actual for the Huber model, with the model's own trend line."""
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    plot_predicted_vs_actual(ax, y_eval, pred_eval, f"Huber: predicted vs actual ({eval_label} lots)")
    compact_legend(ax)
    fig.tight_layout()
    return fig


def draw_huber_curve(table, chosen_alpha, eval_label):
    """Train against evaluation score while the setting alpha changes."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    panels = [("R²", "R² (higher is better)"),
              ("MAE", "MAE in cup points (lower is better)")]
    for ax, (metric, ylabel) in zip(axes, panels):
        ax.plot(table.index, table[f"train {metric}"], marker="o", label="train")
        ax.plot(table.index, table[f"eval {metric}"], marker="o", label=eval_label)
        ax.axvline(chosen_alpha, color="grey", linestyle="--", label=f"chosen alpha = {chosen_alpha:g}")
        ax.set_xscale("log")
        ax.set_xlabel("alpha (log scale): bigger alpha = simpler model")
        ax.set_ylabel(ylabel)
        ax.legend()
    axes[0].set_title("R² against alpha")
    axes[1].set_title("MAE against alpha")
    fig.tight_layout()
    return fig


def draw_linear_regression(y_eval, pred_eval, eval_label, feature, x_feature, y_target):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    # left: the real model, all features together
    plot_predicted_vs_actual(axes[0], y_eval, pred_eval,
                             f"The model, all features: predicted vs actual ({eval_label} lots)")
    compact_legend(axes[0])
    # right: the classic picture, one feature and its line of best fit
    sns.regplot(x=x_feature, y=y_target, scatter_kws={"alpha": 0.35, "s": 14},
                line_kws={"color": "red"}, ax=axes[1])
    axes[1].set_xlabel(feature)
    axes[1].set_ylabel(TARGET)
    axes[1].set_title(f"One feature on its own: {feature} (train lots)")
    fig.tight_layout()
    return fig


def draw_decision_tree(pipe, depth_shown=3):
    tree = pipe.named_steps["model"]
    fig, ax = plt.subplots(figsize=(18, 8))
    plot_tree(tree, max_depth=depth_shown, feature_names=tree_feature_names(pipe),
              filled=True, rounded=True, impurity=False, precision=1, fontsize=11, ax=ax)
    ax.set_title(f"Decision tree: the top {depth_shown} of {tree.get_depth()} levels")
    return fig


def class_metrics(y_specialty, predictions, positive):
    rows = {}
    for name, predicted in predictions.items():
        rows[name] = {
            "Accuracy": accuracy_score(y_specialty, predicted),
            "Precision": precision_score(y_specialty == positive, predicted == positive, zero_division=0),
            "Recall": recall_score(y_specialty == positive, predicted == positive, zero_division=0),
            "F1": f1_score(y_specialty == positive, predicted == positive, zero_division=0),
        }
    return pd.DataFrame(rows).T.round(2)


def draw_class_metrics(table, label):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    table.T.plot.bar(ax=ax, rot=0)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score (cross-validated, 0 to 1)")
    ax.set_title(f"Scores for the class: {label}")
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout()
    return fig


def draw_class_curve(table, name, info, phrase):
    """Train against validation score while ONE setting of the model changes."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    panels = [("accuracy", "accuracy (higher is better)"),
              (f"F1 ({phrase})", f"F1 for the lots that are {phrase}")]
    for ax, (metric, ylabel) in zip(axes, panels):
        ax.plot(table.index, table[f"train {metric}"], marker="o", label="train")
        ax.plot(table.index, table[f"eval {metric}"], marker="o", label="validation")
        ax.axvline(info["chosen"], color="grey", linestyle="--", label=f"chosen = {info['chosen']}")
        if info["log"]:
            ax.set_xscale("log")
        ax.set_xlabel(info["label"])
        ax.set_ylabel(ylabel)
        ax.legend()
    axes[0].set_title(f"{name}: accuracy against the setting")
    axes[1].set_title(f"{name}: F1 against the setting")
    fig.tight_layout()
    return fig


def draw_one_confusion(y_specialty, predicted, name):
    labels = ["below 80", "80 or more"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    ConfusionMatrixDisplay.from_predictions(y_specialty, predicted, display_labels=labels,
                                            cmap="Blues", colorbar=False, ax=axes[0])
    axes[0].set_title(f"{name}: counts of lots")
    ConfusionMatrixDisplay.from_predictions(y_specialty, predicted, display_labels=labels,
                                            normalize="true", values_format=".0%", cmap="Blues",
                                            colorbar=False, ax=axes[1])
    axes[1].set_title("share of each actual group")
    fig.tight_layout()
    return fig


def draw_model_comparison(comparison):
    table = comparison.sort_values("MAE validation", ascending=False)
    positions = np.arange(len(table))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(positions, table["MAE validation"], xerr=table["MAE spread"], alpha=0.8,
            label="validation MAE (mean ± spread)")
    ax.scatter(table["MAE train"], positions, color="black", zorder=3, label="train MAE")
    ax.set_yticks(positions)
    ax.set_yticklabels(table.index)
    ax.set_xlabel("MAE in cup points (lower is better)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False)
    return fig


def draw_cross_validation_scheme(comparison):
    """The 5-fold scheme from the lesson, and what it gives for every model."""
    from matplotlib.patches import Patch, Rectangle
    green, blue, orange, grey = "#b9f0cf", "#9ecbf5", "#f6d8a8", "#eeeeee"
    fig, ax = plt.subplots(figsize=(13, 6.8))
    ax.set_xlim(0, 110)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def box(x, y, w, h, color, text, size=9.5, bold=False):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=color, edgecolor="#555555", linewidth=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size,
                fontweight="bold" if bold else "normal")

    def arrow(x_from, y_from, x_to, y_to):
        ax.annotate("", xy=(x_to, y_to), xytext=(x_from, y_from),
                    arrowprops=dict(arrowstyle="-|>", color="#444444", lw=1.4))

    # all the data: the test lots are put aside first
    box(10, 54, 52, 4, grey, "All data (Arabica lots)")
    box(10, 48.5, 41.6, 4, green, "Training data")
    box(51.6, 48.5, 10.4, 4, orange, "Test data")
    ax.text(56.8, 46.6, "kept aside", ha="center", va="center", fontsize=8.5, color="#555555")

    # the training lots are cut into 5 folds, and each fold takes a turn as the validation fold
    fold_w, gap, x0 = 7.9, 0.5, 10
    for i in range(5):
        box(x0 + i * (fold_w + gap), 41.5, fold_w, 3.6, grey, f"Fold {i + 1}")
    for split in range(5):
        y = 35.5 - split * 5
        ax.text(8.5, y + 1.8, f"Split {split + 1}", ha="right", va="center", fontsize=9.5)
        for i in range(5):
            box(x0 + i * (fold_w + gap), y, fold_w, 3.6, blue if i == split else green, f"Fold {i + 1}")
        arrow(52, y + 1.8, 54.3, y + 1.8)
        box(54.5, y, 7.5, 3.6, "white", f"MAE {split + 1}")
    # the five MAE values are averaged
    ax.plot([63.2, 64.2, 64.2, 63.2], [15.5, 15.5, 39.1, 39.1], color="#444444", lw=1.4)
    arrow(64.2, 27.3, 74.5, 27.3)
    ax.text(69.4, 29.6, "mean of\nthe 5 MAEs", ha="center", va="center", fontsize=9)

    # the final evaluation on the test lots
    ax.text(8.5, 7.7, "Final evaluation", ha="right", va="center", fontsize=9.5)
    box(10, 6, 52, 3.4, orange, "Test data (only used at the end)")

    # every model goes through the same 5 splits, the lowest validation MAE wins
    table = comparison.sort_values("MAE validation")
    ax.text(92.5, 56.5, "Every model goes through the same 5 splits", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.text(92.5, 53.3, "validation MAE (mean ± spread), lowest first", ha="center", va="center",
            fontsize=9, color="#555555")
    for k, (name, row) in enumerate(table.iterrows()):
        y = 46.5 - k * 5.2
        best = k == 0
        ax.add_patch(Rectangle((75, y), 35, 4, facecolor="#fde9a8" if best else "white",
                               edgecolor="#b8860b" if best else "#555555", linewidth=2 if best else 0.8))
        ax.text(76.5, y + 2, name, va="center", fontsize=9.5, fontweight="bold" if best else "normal")
        ax.text(108.5, y + 2, f"{row['MAE validation']:.3f} ± {row['MAE spread']:.3f}", va="center",
                ha="right", fontsize=9.5, fontweight="bold" if best else "normal")
    best_name, best_mae = table.index[0], table["MAE validation"].iloc[0]
    ax.text(92.5, 46.5 - 5 * 5.2 - 4.2, f"Lowest MAE wins: {best_name}, {best_mae:.3f}", ha="center",
            va="center", fontsize=10.5, fontweight="bold")
    arrow(75, 46.5 - 5 * 5.2 - 4.2, 62.6, 7.7)

    ax.legend(handles=[Patch(facecolor=green, edgecolor="#555555", label="training folds: the model learns from these"),
                       Patch(facecolor=blue, edgecolor="#555555", label="validation fold: the model is scored here"),
                       Patch(facecolor=orange, edgecolor="#555555", label="test data: kept aside")],
              loc="upper center", bbox_to_anchor=(0.43, 0.02), ncol=3, frameon=False, fontsize=9)
    fig.tight_layout()
    return fig


def draw_alpha_validation_curve(model, X_train, y_train, cv):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    plot_validation_curve(ax, model, X_train, y_train, cv, "model__alpha",
                          [0.01, 0.1, 1, 10, 100, 1000],
                          "Huber: bigger alpha = simpler model",
                          "alpha (log scale)", log_x=True, scoring="mae")
    ax.legend()
    return fig


def draw_correlation_heatmap(df):
    numbers = df.select_dtypes("number")
    order = numbers.corr()[TARGET].abs().sort_values(ascending=False).index
    corr = numbers[order].corr()
    fig, ax = plt.subplots(figsize=(11, 8.2))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1,
                annot_kws={"size": 10}, ax=ax)
    ax.set_title("Correlation between all numeric columns, strongest link to Total.Cup.Points first")
    fig.tight_layout()
    return fig


def draw_silhouette_by_k(scores_by_k):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(scores_by_k.index, scores_by_k.values, marker="o")
    ax.set_xlabel("number of groups (k)")
    ax.set_ylabel("average silhouette")
    ax.set_title("How many natural groups of lots? (higher is clearer)")
    return fig


def draw_silhouette(X, k):
    labels = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(X)
    values = silhouette_samples(X, labels)
    fig, ax = plt.subplots(figsize=(8, 5))
    start = 10
    for group in range(k):
        group_values = np.sort(values[labels == group])
        end = start + len(group_values)
        ax.fill_betweenx(np.arange(start, end), 0, group_values, alpha=0.7)
        ax.text(-0.05, start + len(group_values) / 2, str(group))
        start = end + 10
    ax.axvline(values.mean(), color="red", linestyle="--", label=f"average {values.mean():.2f}")
    ax.set_xlabel("silhouette value (1 = clearly in its group, below 0 = probably in the wrong group)")
    ax.set_ylabel("group")
    ax.set_yticks([])
    ax.legend()
    ax.set_title(f"Silhouette plot for {k} groups of lots")
    return fig


def draw_predicted_vs_actual(y_test, pred_test):
    mae = mean_absolute_error(y_test, pred_test)
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    plot_predicted_vs_actual(ax, y_test, pred_test, f"Huber on the test lots (MAE {mae:.2f})")
    compact_legend(ax)
    fig.tight_layout()
    return fig


def draw_residuals(y_test, pred_test):
    residuals = y_test - pred_test
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    axes[0].scatter(pred_test, residuals, alpha=0.4, s=14)
    axes[0].axhline(0, color="black", linewidth=1)
    axes[0].set_xlabel("predicted Total.Cup.Points")
    axes[0].set_ylabel("residual = actual − predicted (cup points)")
    axes[0].set_title("Residuals against the prediction")
    sns.histplot(residuals, bins=30, ax=axes[1])
    axes[1].axvline(0, color="black", linewidth=1)
    axes[1].set_xlabel("residual (cup points)")
    axes[1].set_title("How big are the misses?")
    fig.tight_layout()
    return fig


def draw_specialty_confusion(y_test, pred_test):
    actual_specialty = y_test >= 80
    says_specialty = pred_test >= 80
    labels = ["below 80", "80 or more"]
    # a small note in each cell: rows are what the lot really scored, columns what the model said
    cell_notes = [["correct", "false alarm:\nsaid specialty,\nthe cup was not"],
                  ["missed: a specialty lot\nthe model would put\nat the back", "correct"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    counts = ConfusionMatrixDisplay.from_predictions(actual_specialty, says_specialty, display_labels=labels,
                                                     cmap="Blues", colorbar=False, ax=axes[0])
    axes[0].set_title("Counts of lots (test set)")
    shares = ConfusionMatrixDisplay.from_predictions(actual_specialty, says_specialty, display_labels=labels,
                                                     normalize="true", values_format=".0%", cmap="Blues",
                                                     colorbar=False, ax=axes[1])
    axes[1].set_title("Share of each actual group")
    for display in (counts, shares):
        for row in range(2):
            for col in range(2):
                number = display.text_[row, col]
                number.set_position((col, row - 0.12))          # the number moves up a little
                display.ax_.text(col, row + 0.08, cell_notes[row][col], ha="center", va="top",
                                 fontsize=8.5, color=number.get_color())
    fig.tight_layout()
    return fig


def draw_importance(table):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(table["feature"], table["MAE gets worse by"], xerr=table["spread"])
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("how much the MAE gets worse when this column is shuffled (cup points)")
    ax.set_title("What drives the predictions (test lots)")
    fig.tight_layout()
    return fig


def draw_learning_curve(model, X_train, y_train, cv, baseline_mae):
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_learning_curve(ax, model, X_train, y_train, cv, "Would more lots help?",
                        RANDOM_STATE, scoring="mae")
    ax.axhline(baseline_mae, color="grey", linestyle="--", linewidth=1,
               label="baseline: always guess the average")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
    fig.tight_layout()
    return fig


# ------------------------------------------------------------------
# DATA AND MODEL (loaded once, then remembered by Streamlit)
# ------------------------------------------------------------------
@st.cache_resource
def load_everything():
    model = joblib.load(MODEL_PATH)
    df = load_arabica(PATHS["clean_data"])
    numeric_cols, categorical_cols = get_feature_columns(df)
    X_train, X_test, y_train, y_test = split_once(df, RANDOM_STATE)
    cv = make_cv(RANDOM_STATE)
    baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
    return {
        "model": model, "df": df, "cv": cv, "features": numeric_cols + categorical_cols,
        "X_train": X_train, "X_test": X_test, "y_train": y_train, "y_test": y_test,
        "pred_test": model.predict(X_test),
        "pred_baseline": baseline.predict(X_test),
    }


@st.cache_data
def cv_scores():
    d = load_everything()
    base = -cross_val_score(DummyRegressor(strategy="mean"), d["X_train"], d["y_train"],
                            cv=d["cv"], scoring="neg_mean_absolute_error")
    final = -cross_val_score(d["model"], d["X_train"], d["y_train"],
                             cv=d["cv"], scoring="neg_mean_absolute_error")
    return base.mean(), base.std(), final.mean(), final.std()


@st.cache_data
def importance_table():
    d = load_everything()
    result = permutation_importance(d["model"], d["X_test"], d["y_test"],
                                    scoring="neg_mean_absolute_error", n_repeats=30,
                                    random_state=RANDOM_STATE, n_jobs=1)
    table = pd.DataFrame({"feature": d["X_test"].columns,
                          "MAE gets worse by": result.importances_mean,
                          "spread": result.importances_std})
    return table.sort_values("MAE gets worse by")


def regressor_key():
    """The models and their settings as text. Streamlit remembers a result per input, so passing
    this to the two cached functions below makes them refit when a model is added or changed."""
    return tuple(f"{name}: {regressor!r}" for name, regressor in make_regressors().items())


@st.cache_resource
def fitted_regressors(model_key):
    d = load_everything()
    numeric_cols, categorical_cols = get_feature_columns(d["df"])
    fitted = {}
    for name, regressor in make_regressors().items():
        pipe = build_pipeline(regressor, numeric_cols, categorical_cols)
        fitted[name] = pipe.fit(d["X_train"], d["y_train"])
    return fitted


@st.cache_data
def regression_results(model_key):
    d = load_everything()
    results = {}
    for name, pipe in fitted_regressors(model_key).items():
        results[name] = {
            "train": pipe.predict(d["X_train"]),                                           # the lots it was fitted on
            "validation": cross_val_predict(pipe, d["X_train"], d["y_train"], cv=d["cv"]),  # each lot predicted by a model that did not see it
            "test": pipe.predict(d["X_test"]),                                             # the test lots
        }
    return results


@st.cache_data
def knn_curve(eval_key):
    """Train and evaluation score of KNN for every number of neighbours in KNN_SETTINGS."""
    d = load_everything()
    numeric_cols, categorical_cols = get_feature_columns(d["df"])
    rows = []
    for k in KNN_SETTINGS:
        pipe = build_pipeline(KNeighborsRegressor(n_neighbors=k), numeric_cols, categorical_cols)
        pipe.fit(d["X_train"], d["y_train"])
        train_pred = pipe.predict(d["X_train"])
        if eval_key == "test":
            y_eval, eval_pred = d["y_test"], pipe.predict(d["X_test"])
        else:
            # each lot predicted by a model that did not see it
            y_eval = d["y_train"]
            eval_pred = cross_val_predict(pipe, d["X_train"], d["y_train"], cv=d["cv"])
        rows.append({"k": k,
                     "train R²": r2_score(d["y_train"], train_pred),
                     "eval R²": r2_score(y_eval, eval_pred),
                     "train MAE": mean_absolute_error(d["y_train"], train_pred),
                     "eval MAE": mean_absolute_error(y_eval, eval_pred)})
    return pd.DataFrame(rows).set_index("k")


@st.cache_data
def huber_curve(eval_key):
    """Train and evaluation score of Huber for every alpha in HUBER_ALPHAS."""
    d = load_everything()
    numeric_cols, categorical_cols = get_feature_columns(d["df"])
    rows = []
    for alpha in HUBER_ALPHAS:
        pipe = build_pipeline(HuberRegressor(alpha=alpha, epsilon=1.35, max_iter=1000),
                              numeric_cols, categorical_cols)
        pipe.fit(d["X_train"], d["y_train"])
        train_pred = pipe.predict(d["X_train"])
        if eval_key == "test":
            y_eval, eval_pred = d["y_test"], pipe.predict(d["X_test"])
        else:
            # each lot predicted by a model that did not see it
            y_eval = d["y_train"]
            eval_pred = cross_val_predict(pipe, d["X_train"], d["y_train"], cv=d["cv"])
        rows.append({"alpha": alpha,
                     "train R²": r2_score(d["y_train"], train_pred),
                     "eval R²": r2_score(y_eval, eval_pred),
                     "train MAE": mean_absolute_error(d["y_train"], train_pred),
                     "eval MAE": mean_absolute_error(y_eval, eval_pred)})
    return pd.DataFrame(rows).set_index("alpha")


@st.cache_data
def class_predictions():
    """Yes/no predictions at the chosen setting of each model. Every lot is predicted by a
    model that did not see it (cross-validation on the training lots)."""
    d = load_everything()
    X_train, y_train, cv = d["X_train"], d["y_train"], d["cv"]
    numeric_cols, categorical_cols = get_feature_columns(d["df"])
    y_specialty = (y_train >= 80).to_numpy()          # True = 80 or more, False = below 80
    predictions = {}
    for name in ["Majority class (baseline)", "K-nearest neighbours", "Logistic regression"]:
        setting = CLASS_SETTINGS.get(name, {}).get("chosen")
        pipe = class_model_at(name, setting, numeric_cols, categorical_cols)
        predictions[name] = cross_val_predict(pipe, X_train, y_specialty, cv=cv)
    # Huber is a regression model: its predicted score is cut at 80, shown as a comparison only
    predictions["Huber regression, cut at 80"] = cross_val_predict(d["model"], X_train, y_train, cv=cv) >= 80
    return y_specialty, predictions


@st.cache_data
def class_curve(name):
    """Train and validation score of one model for every value of its setting."""
    d = load_everything()
    X_train, y_train, cv = d["X_train"], d["y_train"], d["cv"]
    numeric_cols, categorical_cols = get_feature_columns(d["df"])
    y_specialty = (y_train >= 80).to_numpy()
    rows = []
    for setting in CLASS_SETTINGS[name]["values"]:
        pipe = class_model_at(name, setting, numeric_cols, categorical_cols)
        pipe.fit(X_train, y_specialty)
        train_pred = pipe.predict(X_train)
        eval_pred = cross_val_predict(pipe, X_train, y_specialty, cv=cv)
        rows.append({
            "setting": setting,
            "train accuracy": accuracy_score(y_specialty, train_pred),
            "eval accuracy": accuracy_score(y_specialty, eval_pred),
            "train F1 (below 80)": f1_score(~y_specialty, ~train_pred, zero_division=0),
            "eval F1 (below 80)": f1_score(~y_specialty, ~eval_pred, zero_division=0),
            "train F1 (80 or more)": f1_score(y_specialty, train_pred, zero_division=0),
            "eval F1 (80 or more)": f1_score(y_specialty, eval_pred, zero_division=0),
        })
    return pd.DataFrame(rows).set_index("setting")


@st.cache_data
def part_score_matrix():
    d = load_everything()
    columns = [c for c in PART_SCORES if c in d["df"].columns]
    return StandardScaler().fit_transform(d["df"][columns].dropna())


@st.cache_data
def silhouette_by_k():
    X = part_score_matrix()
    values = {}
    for k in range(2, 9):
        labels = KMeans(n_clusters=k, n_init=10, random_state=RANDOM_STATE).fit_predict(X)
        values[k] = silhouette_score(X, labels)
    return pd.Series(values, name="average silhouette")


d = load_everything()
model, df, cv, features = d["model"], d["df"], d["cv"], d["features"]
X_train, X_test, y_train, y_test = d["X_train"], d["X_test"], d["y_train"], d["y_test"]
pred_test, pred_baseline = d["pred_test"], d["pred_baseline"]
test_mae = mean_absolute_error(y_test, pred_test)
baseline_test_mae = mean_absolute_error(y_test, pred_baseline)


# ------------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------------
PAGES = [
    "Cover",
    "1 · The question",
    "2 · The data",
    "3 · Metric and baseline",
    "4 · Models compared",
    "5 · Final model",
    "6 · Where it goes wrong",
    "7 · What drives it",
    "8 · Demo",
    "9 · Coffee globe",
    "10 · Limits and conclusions",
    "11 · Thank you",
    "References",
]
(P_COVER, P_QUESTION, P_DATA, P_METRIC, P_MODELS, P_FINAL,
 P_ERRORS, P_DRIVERS, P_DEMO, P_GLOBE, P_LIMITS, P_THANKS, P_REFS) = PAGES
page = st.sidebar.radio("Presentation", PAGES)


# ------------------------------------------------------------------
# PAGES
# ------------------------------------------------------------------
if page == P_COVER:
    st.markdown(f"""
<div style="text-align:center; min-height:68vh; display:flex; flex-direction:column; justify-content:center;">
<h1 style="font-size:3.4rem;">{PROJECT_TITLE}</h1>
<h3>Predicting the cupping score of green coffee with machine learning</h3>
<p style="margin-top:3rem;">Project 2 · Machine Learning: From Data to Predictions<br>
Ironhack · Data Science &amp; Machine Learning</p>
<p><b>{PRESENTER}</b> · October 2026</p>
</div>
""", unsafe_allow_html=True)

elif page == P_QUESTION:
    st.title("What makes a green coffee score higher?")
    st.subheader("Where the idea started")
    st.markdown("""
- A **green bean identifier**: upload a photo, or point a live camera at a bean, and see the
  information about that specific green bean on screen, live.
- Going further: connect it to **smart glasses** such as the Ray-Ban Meta, to capture a bean and
  view the coffee information in a virtual or augmented-reality style experience.
""")
    st.subheader("What it needs")
    st.markdown("""
- A **database** of the characteristics that make up the average green bean, and the average of
  each specific content of the bean.
- That led us to use the **cup score (Total Cup Points) as the target**, so machine-learning
  models can learn how a bean's characteristics relate to its quality.
""")
    st.subheader("The question for the ML project")
    st.write("Can we predict a green coffee's Total Cup Points from facts known before it is "
             "cupped: origin, variety, processing method, altitude, moisture, defects and colour?")
    # DRAFT - rewrite in your own words, using the framing from notebook 01
    st.write("**Who uses it and for what decision:** a buyer deciding which lots to taste first.")

elif page == P_DATA:
    st.title("The data")
    st.write(f"{df.shape[0]} Arabica lots, {df.shape[1]} columns. One row is one sample of "
             "green coffee that a grader cupped. The target is its Total.Cup.Points. "
             "Source and licence are on the References page.")
    data_blocks = [DATA_CALL, source_of(load_arabica)]
    (tab_raw, tab_eda, tab_score, tab_country,
     tab_features, tab_missing) = st.tabs(["Raw datasets", "EDA & Cleaning", "Score distribution",
                                           "Score by country", "Altitude and moisture", "Missing values"])

    with tab_raw:
        st.write("The original files, before any cleaning. Click a title to open it. The tables "
                 "scroll, and the column titles stay on top while you scroll down. The datasets are "
                 "listed alphabetically.")
        raw_files = sorted(RAW_FOLDER.rglob("*.csv")) if RAW_FOLDER.exists() else []
        sources = load_sources()
        if not raw_files:
            st.info("No CSV files found in data/raw.")
        raw_items = []
        for path in raw_files:
            try:
                raw_df = read_raw(str(path))
            except Exception as error:
                st.warning(f"{path.name} could not be read: {error}")
                continue
            source = find_dataset_source(path.name, sources)
            raw_items.append((friendly_source_name(path, source), path, raw_df, source))
        # A to Z by the name shown on the title (capitals ignored); the file name settles a tie
        raw_items.sort(key=lambda item: (item[0].lower(), item[1].name.lower()))
        for title, path, raw_df, source in raw_items:
            hidden = [c for c in raw_df.columns if any(w in str(c).lower() for w in PERSONAL_WORDS)]
            with st.expander(f"{title} · {len(raw_df):,} rows × {raw_df.shape[1]} columns"):
                if source and source.get("url"):
                    licence = clean_text(source.get("licence"))
                    st.markdown(f"**Source:** [{clean_text(source.get('title'))}]({source['url']})"
                                + (f" · Licence: {licence}" if licence else ""))
                st.caption(f"File: {path.relative_to(ROOT)} · {len(raw_df):,} rows × "
                           f"{raw_df.shape[1]} columns.")
                if hidden:
                    st.caption(f"{len(hidden)} columns with personal data (names, contacts, addresses) "
                               f"are hidden here and never reach the clean table: {', '.join(map(str, hidden))}")
                st.dataframe(raw_df.drop(columns=hidden).head(MAX_ROWS_SHOWN), height=350)
                if len(raw_df) > MAX_ROWS_SHOWN:
                    st.caption(f"Showing the first {MAX_ROWS_SHOWN:,} rows.")

    with tab_eda:
        st.subheader("How SQL matched the tables")
        # DRAFT - rewrite in your own words
        st.write("The raw CQI data comes as two files, Arabica and Robusta, with different column "
                 "names and with personal-data columns. SQL did the matching: `SELECT` with explicit "
                 "columns keeps only what we need, columns that mean the same thing get the same name, "
                 "and `UNION ALL` stacks the two files into one clean table with a `species` column. "
                 "Where a Robusta column match was only a guess, the value was left empty. Anything "
                 "that learns from the data (filling gaps, scaling, encoding) waits for the pipeline "
                 "after the split, so nothing leaks from the test set.")
        files = sql_files()
        if files:
            used = sql_functions_used(files)
            if not used.empty:
                st.markdown("**SQL functions found in the files**")
                st.dataframe(used, hide_index=True)
            for path in files:
                with st.expander(f"SQL file: {path.name}"):
                    st.code(path.read_text(), language="sql")
        else:
            st.info("No .sql files found in src/sql.")

        st.subheader("The cleaning log")
        if CLEANING_REPORT_PATH.exists():
            report = json.loads(CLEANING_REPORT_PATH.read_text())
            steps = report.get("steps", report) if isinstance(report, dict) else report
            try:
                st.dataframe(pd.json_normalize(steps), hide_index=True)
            except Exception:
                st.json(report)

        st.subheader("What I found and what I did about it")
        st.markdown("""
- 252 Arabica rows had moisture of exactly 0.0, which means "not measured". I set them to empty.
- 38 rows had moisture between 0.01 and 0.05, which is impossible for green coffee. I set them to empty.
- Altitude above 3,000 m (14 rows) and below 50 m (17 rows) were typing errors. I set them to empty.
- One row with a total score of 0 was dropped.
- Gaps are filled later inside the pipeline, learning from the training set only.
""")

        st.subheader("ERD")
        erd_images = find_erd_images()
        if erd_images:
            for image in erd_images:
                st.image(str(image), caption=image.name)
        else:
            st.info("No ERD image yet. Save it as images/erd.png in the project folder, then rerun.")

    with tab_score:
        st.subheader("Two features and the score, in 3D")
        if px is None:
            st.info("The 3D diagram needs the plotly library. In the terminal run "
                    "`python -m pip install plotly`, then restart the app.")
        else:
            numeric_cols, _ = get_feature_columns(df)
            # the two numeric features most linked to the score are the default axes
            ranked = df[numeric_cols].corrwith(df[TARGET]).abs().sort_values(ascending=False).index.tolist()
            axis_x, axis_y, axis_color = st.columns(3)
            x_feature = axis_x.selectbox("X axis", numeric_cols, index=numeric_cols.index(ranked[0]))
            y_feature = axis_y.selectbox("Y axis", numeric_cols, index=numeric_cols.index(ranked[1]))
            color_by = axis_color.selectbox("Colour by", [TARGET, "Processing.Method", "Color",
                                                          "Country.of.Origin", "Variety"])
            # a narrow column on the left holds the toggle, the diagram takes the rest of the width
            toggle_side, chart_side = st.columns([1, 5])
            show_line = toggle_side.toggle("Show the 80-point specialty line", value=False)
            chart_side.plotly_chart(draw_score_3d(df, x_feature, y_feature, color_by, show_line),
                                    width="stretch")
            code_box(data_blocks, draw_score_3d, model_title="1. The data behind it")

        st.subheader("How the scores are spread")
        show_plot(draw_score_distribution(df))
        st.caption(f"{(df[TARGET] < 80).mean() * 100:.1f}% of lots score below 80 points.")
        code_box(data_blocks, draw_score_distribution, model_title="1. The data behind it")
    with tab_country:
        show_plot(draw_score_by_country(df))
        code_box(data_blocks, draw_score_by_country, model_title="1. The data behind it")
    with tab_features:
        show_plot(draw_altitude_moisture(df))
        code_box(data_blocks, draw_altitude_moisture, model_title="1. The data behind it")
    with tab_missing:
        show_plot(draw_missing_values(df, features))
        code_box(data_blocks, draw_missing_values, model_title="1. The data behind it")

elif page == P_METRIC:
    st.title("Metric and baseline")
    st.write("**Metric: MAE**, the average miss in cup points. It is easy to explain and is not "
             "dominated by a few extreme scores. R² (the share of the variation we explain) is "
             "reported next to it.")
    # DRAFT - check it against your histogram on page 2
    st.write("**Which mistake costs more:** specialty coffee starts at about 80 points and most "
             "scores cluster just above it, so a miss of 1 to 2 points can move many coffees "
             "across that line.")
    base_mean, base_std, final_mean, final_std = cv_scores()
    col1, col2 = st.columns(2)
    col1.metric("Baseline MAE (always guess the average)", f"{base_mean:.2f} ± {base_std:.2f}")
    col2.metric("Huber MAE (cross-validated)", f"{final_mean:.2f} ± {final_std:.2f}")
    st.caption("Cross-validated on the training lots only, 5 folds, mean ± spread.")
    code_box([BASELINE_CODE, FINAL_MODEL_CODE], model_title="1. The baseline and the cross-validation",
             label="Show the code behind these numbers")

    tab_heat, tab_line, tab_class = st.tabs(
        ["Correlation heatmap", "Regression Evaluation", "Classification Evaluation"])

    with tab_heat:
        st.write("How every numeric column moves together, with the columns ordered by how strongly "
                 "they move with Total.Cup.Points.")
        with st.container(key="tall_plot"):          # this chart may be taller (see PRESENTATION_CSS)
            show_plot(draw_correlation_heatmap(df))
        st.caption("The ten part scores add up to the total, so they correlate strongly with it by "
                   "construction. The model does not use them, only the bean and origin measurements.")
        code_box([DATA_CALL, source_of(load_arabica)], draw_correlation_heatmap,
                 model_title="1. The data behind it")

    with tab_line:
        st.write("Because the target is a number, this is a regression problem. Four models are "
                 "scored with the four standard regression figures, and each one gets the diagram "
                 "that suits it:")
        st.markdown("""
- **MSE:** the average of the squared misses, so one big miss counts extra.
- **RMSE:** the square root of the MSE, back in cup points. It is never smaller than the MAE.
- **MAE:** the average miss in cup points, our main metric.
- **R²:** the share of the variation in scores the model explains (0 means no better than guessing the average).
""")
        st.caption("KNN works by distance, so every number is put on one scale first. The "
                   "StandardScaler inside the pipeline does that, for all four models, so the "
                   "comparison is fair. The tree's depth is capped so that it does not memorise the lots.")
        eval_choice = st.radio("Score on",
                               ["Validation lots (cross-validation on the training lots)",
                                "Test lots (uses the test set again)"], horizontal=True)
        eval_key = "test" if eval_choice.startswith("Test") else "validation"
        eval_label = "test" if eval_key == "test" else "validation"
        y_eval = y_test if eval_key == "test" else y_train
        results = regression_results(regressor_key())
        fitted = fitted_regressors(regressor_key())
        numeric_cols, _ = get_feature_columns(df)

        st.subheader("The four models side by side")
        side_by_side = pd.DataFrame({name: regression_figures(y_eval, r[eval_key])
                                     for name, r in results.items()}).T.round(2)
        st.dataframe(side_by_side)

        score_blocks = {
            "The models": source_of(make_regressors),
            "Scaling and encoding": source_of(build_pipeline, make_preprocessor),
            "Fitting and scoring": source_of(fitted_regressors, regression_results, regression_figures),
        }

        for name, r in results.items():
            st.subheader(name)
            figures = regression_figures(y_eval, r[eval_key])
            for column, (label, value) in zip(st.columns(4), figures.items()):
                column.metric(label, f"{value:.2f}")
            train_figures = regression_figures(y_train, r["train"])
            st.caption("On the train lots: " + " · ".join(f"{label} {value:.2f}"
                                                         for label, value in train_figures.items()))

            if name == "K-nearest neighbours":
                chosen_k = make_regressors()[name].n_neighbors
                st.caption(f"The KNN diagram: the setting k (how many neighbours vote) on the x axis, "
                           f"the score on the y axis, the train lots against the {eval_label} lots. "
                           f"For regression R² plays the role of accuracy. At k = 1 every lot is its own "
                           f"nearest neighbour, so the train score is almost perfect but the model is "
                           f"memorising. More neighbours make a simpler model. The dashed line marks "
                           f"the k = {chosen_k} used in the figures above.")
                show_plot(draw_knn_curve(knn_curve(eval_key), chosen_k, eval_label))
                code_box(score_blocks, knn_curve, draw_knn_curve,
                         model_title="1. The model, the pipeline and the scoring (one tab each)",
                         draw_title="2. The code that computes and draws the diagram")

            elif name == "Linear regression":
                strongest = X_train[numeric_cols].corrwith(y_train).abs().idxmax()
                strongest_r = X_train[strongest].corr(y_train)
                st.caption(f"Left: the actual model, with all eight features together. The closer its "
                           f"trend is to the perfect line, the better. Right: the same idea with one "
                           f"feature only, {strongest}, the numeric feature most linked to the score "
                           f"(correlation {strongest_r:.2f}). One feature alone explains little.")
                show_plot(draw_linear_regression(y_eval, r[eval_key], eval_label,
                                                 strongest, X_train[strongest], y_train))
                code_box(score_blocks, draw_linear_regression, compact_legend, plot_predicted_vs_actual,
                         model_title="1. The model, the pipeline and the scoring (one tab each)",
                         draw_title="2. The code that draws the diagram")

            elif name.startswith("Huber"):
                chosen_alpha = make_regressors()[name].alpha
                st.caption(f"Huber is the final model and it is a regression: it predicts the cup score as "
                           f"a number. It counts small misses by their square and big misses only by their "
                           f"size (epsilon = 1.35 sets how big a miss has to be before it counts only by "
                           f"its size), so a few very low scores pull the line around less. First "
                           f"diagram: predicted against actual on the {eval_label} lots, where the closer "
                           f"the trend is to the perfect line, the better. Second diagram: the setting "
                           f"alpha on the x axis, the score on the y axis, the train lots against the "
                           f"{eval_label} lots. For regression R² plays the role of accuracy. A bigger "
                           f"alpha holds the line back, which makes a simpler model. The dashed line marks "
                           f"the alpha = {chosen_alpha:g} used in the figures above.")
                show_plot(draw_huber_fit(y_eval, r[eval_key], eval_label))
                show_plot(draw_huber_curve(huber_curve(eval_key), chosen_alpha, eval_label))
                code_box(score_blocks, huber_curve, draw_huber_curve, draw_huber_fit,
                         compact_legend, plot_predicted_vs_actual,
                         model_title="1. The model, the pipeline and the scoring (one tab each)",
                         draw_title="2. The code that draws the diagrams")

            else:
                st.caption("How to read it: each box asks a yes/no question about one feature (True goes "
                           "left). `value` is the average cup score of the lots in that box and "
                           "`samples` is how many lots are in it. Numbers in the questions are in scaled "
                           "units, because the pipeline puts every number on one scale.")
                show_plot(draw_decision_tree(fitted[name]))
                code_box(score_blocks, draw_decision_tree, tree_feature_names,
                         model_title="1. The model, the pipeline and the scoring (one tab each)",
                         draw_title="2. The code that draws the diagram")

    with tab_class:
        st.write("Asked as a yes/no question at the 80-point line (80 or more, or below 80), the same "
                 "problem becomes a classification problem, scored with accuracy, precision, recall "
                 "and F1. Every lot is predicted by a model that did not see it "
                 "(cross-validation on the training lots), so the test set stays untouched. Each "
                 "model gets the same lesson-style diagram: the score on the y axis, the model's own "
                 "setting on the x axis, train against validation.")
        y_specialty, predictions = class_predictions()
        positive_label = st.radio("Which lots should the scores be about?",
                                  ["Below 80 (the lots to catch)", "80 or more (specialty)"],
                                  horizontal=True)
        positive = positive_label.startswith("80")
        phrase = "80 or more" if positive else "below 80"
        st.markdown(f"""
- **Precision:** of the lots a model stamps "{phrase}", how many really are.
- **Recall:** of all the lots that really are "{phrase}", how many the model catches.
- **F1:** one number that is low when either precision or recall is low.
""")
        metrics_table = class_metrics(y_specialty, predictions, positive)

        st.subheader("The models side by side")
        st.dataframe(metrics_table)
        show_plot(draw_class_metrics(metrics_table, positive_label))
        code_box([source_of(class_predictions)], class_metrics, draw_class_metrics,
                 model_title="1. The models (cross-validated predictions)",
                 draw_title="2. The code that scores and draws it")
        st.caption("The majority-class baseline always gives the most common answer, so it has no "
                   "setting to vary and no diagram of its own. Huber regression is a regression model, "
                   "so it appears here only as a comparison, with its predicted score cut at 80. Its "
                   "own diagrams are on the Regression Evaluation tab.")

        class_blocks = {
            "The classifiers": source_of(class_model_at),
            "Scaling and encoding": source_of(build_pipeline, make_preprocessor),
            "Fitting and scoring": source_of(class_predictions, class_curve),
        }

        for name, info in CLASS_SETTINGS.items():
            st.subheader(name)
            row = metrics_table.loc[name]
            for column, label in zip(st.columns(4), ["Accuracy", "Precision", "Recall", "F1"]):
                column.metric(label, f"{row[label]:.2f}")
            st.caption(info["explain"])
            show_plot(draw_class_curve(class_curve(name), name, info, phrase))
            code_box(class_blocks, draw_class_curve,
                     model_title="1. The model, the pipeline and the scoring (one tab each)",
                     draw_title="2. The code that draws the diagram")
            show_plot(draw_one_confusion(y_specialty, predictions[name], name))
            code_box([source_of(class_predictions)], draw_one_confusion,
                     model_title="1. The model (cross-validated predictions)",
                     label="Show the code behind this confusion matrix")

elif page == P_MODELS:
    st.title("What I tried")
    st.write("Same 5 cross-validation folds for every model. The bar is the validation MAE with "
             "its spread, the black dot is the training MAE.")
    show_plot(draw_model_comparison(COMPARISON))
    gap = (COMPARISON["MAE validation"] - COMPARISON["MAE train"]).drop("Baseline (mean)")
    st.caption(f"The biggest gap between train and validation is {gap.idxmax()}: "
               "the model is memorising the training lots.")
    code_box(MODEL_CODE, draw_model_comparison,
             model_title="1. The code for each model (one tab each)")

    st.subheader("How each model is tested")
    st.write("Every model is tested the same way, so the comparison is fair. The test lots are put "
             "aside first. The training lots are cut into 5 folds. In each of the 5 splits one fold "
             "(blue) is held back and the model learns from the other four (green), then it is "
             "scored on the held-back fold. That gives 5 MAE values, and their mean is the "
             "validation MAE of the model. The model with the lowest validation MAE is the one we "
             "choose. The test lots are only used at the end, for the final evaluation.")
    show_plot(draw_cross_validation_scheme(COMPARISON))
    st.caption("The same 5 splits are used for every model, so a difference in MAE comes from the "
               "model and not from the luck of the split. The numbers on the right are the "
               "validation MAE and its spread from the bar chart above.")
    code_box([MODEL_CODE["How they are scored"]], draw_cross_validation_scheme,
             model_title="1. How each model is scored (the same 5 folds)")

    st.subheader("The final model: Huber regression, alpha = 10")
    st.write("Huber is a linear model that counts small misses by their square but big misses "
             "only by their size, so a few very low scores pull the line around less. In "
             "cross-validation it beat Ridge on all 5 folds (MAE 1.596 against 1.647) and tied "
             "the tuned random forest (1.597, the best of 48 settings tried), so I chose the "
             "linear model I can explain. On the test lots the two had almost the same MAE.")
    show_plot(draw_alpha_validation_curve(model, X_train, y_train, cv))
    code_box([MODEL_CODE["Huber"]], draw_alpha_validation_curve, plot_validation_curve,
             model_title="1. The model whose alpha changes")

elif page == P_FINAL:
    st.title("The final model")
    base_mean, base_std, final_mean, final_std = cv_scores()
    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline MAE (cross-validated)", f"{base_mean:.2f}")
    col2.metric("Huber MAE (cross-validated)", f"{final_mean:.2f}")
    col3.metric("Huber MAE on the test lots", f"{test_mae:.2f}")
    st.caption(f"R² on the test lots: {r2_score(y_test, pred_test):.2f}. "
               f"{len(y_test)} test lots, split with random_state={RANDOM_STATE}. "
               "These numbers should match notebook 03. The test lots were scored for both Ridge "
               "and Huber; Huber was chosen from the cross-validation.")
    show_plot(draw_predicted_vs_actual(y_test, pred_test))
    st.caption("The closer the model's trend is to the perfect line, the better the predictions. "
               "A flatter trend means the model pulls every lot toward the average score.")
    code_box([FINAL_MODEL_CODE, source_of(build_pipeline, make_preprocessor), saved_model_text(model)],
             draw_predicted_vs_actual, compact_legend, plot_predicted_vs_actual)

elif page == P_ERRORS:
    st.title("Where it goes wrong")
    residuals = y_test - pred_test
    show_plot(draw_residuals(y_test, pred_test))
    code_box([PREDICT_CODE], draw_residuals)
    st.write(f"The typical miss is {test_mae:.2f} cup points, and the biggest miss on the test "
             f"lots is {residuals.abs().max():.1f} points.")
    # DRAFT - check it against your plots, then reword
    st.write("**Business reading:** use it to decide what to taste first, not to screen lots out.")

    st.subheader("The 80-point line")
    actual_specialty = y_test >= 80
    says_specialty = pred_test >= 80
    st.write(f"Right side of the 80 line: **{accuracy_score(actual_specialty, says_specialty):.1%}**. "
             f"Always saying 'specialty' with no model at all: {actual_specialty.mean():.1%}. "
             f"Sub-80 lots caught: {recall_score(~actual_specialty, ~says_specialty):.0%}. "
             f"Flagged lots that really are sub-80: "
             f"{precision_score(~actual_specialty, ~says_specialty, zero_division=0):.0%}.")
    show_plot(draw_specialty_confusion(y_test, pred_test))
    code_box([PREDICT_CODE], draw_specialty_confusion)

    st.subheader("Error by country")
    st.dataframe(error_by_group(X_test["Country.of.Origin"], y_test, pred_test, min_lots=10))
    code_box([PREDICT_CODE], error_by_group, draw_title="2. The code that builds the table",
             label="Show the code behind this table")

elif page == P_DRIVERS:
    st.title("What drives the predictions")
    show_plot(draw_importance(importance_table()))
    st.write("Each column is shuffled in turn to see how much the average miss grows. "
             "Read with care: this shows what the model uses, not what causes a high score.")
    code_box([saved_model_text(model)], importance_table, draw_importance,
             model_title="1. The model being explained",
             draw_title="2. The code that computes and draws it")

elif page == P_DEMO:
    st.title(DEMO_TITLE)
    tab_new, tab_real = st.tabs(["Score a new coffee", "Check a real test lot"])

    with tab_new:
        left, right = st.columns(2)
        with left:
            country = st.selectbox("Country of origin", sorted(df["Country.of.Origin"].dropna().unique()))
            variety = st.selectbox("Variety", sorted(df["Variety"].dropna().unique()))
            process = st.selectbox("Processing method", sorted(df["Processing.Method"].dropna().unique()))
            color = st.selectbox("Bean colour", sorted(df["Color"].dropna().unique()))
        with right:
            altitude_known = st.checkbox("Altitude is known", value=False)
            altitude = st.number_input("Mean altitude (m)", min_value=50, max_value=3000,
                                       value=1200, step=50, disabled=not altitude_known)
            moisture_known = st.checkbox("Moisture was measured", value=False)
            moisture = st.number_input("Moisture", min_value=0.05, max_value=0.3,
                                       value=0.11, step=0.01, disabled=not moisture_known)
            defects_one = st.number_input("Category one defects", min_value=0, max_value=50, value=0)
            defects_two = st.number_input("Category two defects", min_value=0, max_value=100, value=0)

        if st.button("Predict cup score"):
            new_row = pd.DataFrame([{
                "Country.of.Origin": country,
                "Variety": variety,
                "Processing.Method": process,
                "Moisture": moisture if moisture_known else np.nan,
                "Category.One.Defects": defects_one,
                "Category.Two.Defects": defects_two,
                "Color": color,
                "altitude_mean_meters": altitude if altitude_known else np.nan,
            }])
            prediction = model.predict(new_row)[0]
            st.metric("Predicted Total Cup Points", f"{prediction:.1f}")
            st.write("Predicted side of the 80-point line:",
                     "80 or more" if prediction >= 80 else "below 80")
            st.caption(f"Typical miss on the test lots: about {test_mae:.2f} cup points, "
                       "so read this as an estimate, not a verdict. Missing values are filled "
                       "by the pipeline, the same way as in training.")
            st.dataframe(new_row)
        code_box([DEMO_CODE], model_title="1. The code behind the prediction",
                 label="Show the code behind this prediction")

    with tab_real:
        st.write("A lot the model never saw in training: its real cupping score against the "
                 "model's prediction.")
        lot_id = st.selectbox("Pick a test lot (row number)", list(X_test.index))
        lot = X_test.loc[[lot_id]]
        predicted = model.predict(lot)[0]
        actual = y_test.loc[lot_id]
        c1, c2, c3 = st.columns(3)
        c1.metric("Actual score (cupped)", f"{actual:.1f}")
        c2.metric("Model's prediction", f"{predicted:.1f}")
        c3.metric("Miss", f"{actual - predicted:+.1f}")
        st.dataframe(lot)
        code_box([REAL_LOT_CODE], model_title="1. The code behind the prediction",
                 label="Show the code behind this prediction")

elif page == P_GLOBE:
    st.title("Coffee globe")
    if (ROOT / "static" / "globe" / "coffee_globe.html").exists():
        st.iframe(f"{GLOBE_URL}?v={int((ROOT / 'static' / 'globe' / 'coffee_globe.html').stat().st_mtime)}", height=750)  # the file's time in the URL, so a re-sync is picked up without a hard refresh
        st.caption("The globe loads its map from the internet, so check your wifi before presenting.")
    else:
        st.warning("The globe is not set up for Streamlit yet. Run these commands in the "
                   "terminal from the project folder, then restart the app.")
        st.code("""mkdir -p static .streamlit
cp -R globe static/globe
echo "[server]" > .streamlit/config.toml
echo "enableStaticServing = true" >> .streamlit/config.toml""", language="bash")

elif page == P_LIMITS:
    st.title("Limits and conclusions")
    # DRAFT - the numbers update by themselves; check the wording, then reword in your own voice
    gain = baseline_test_mae - test_mae
    r2 = r2_score(y_test, pred_test)
    drivers = importance_table().sort_values("MAE gets worse by", ascending=False)
    top_drivers = [str(name).replace(".", " ").replace("_", " ") for name in drivers["feature"].head(3)]
    gap_moisture = df["Moisture"].isna().mean()
    gap_altitude = df["altitude_mean_meters"].isna().mean()
    lots_by_country = df["Country.of.Origin"].value_counts()
    indonesia_lots = int(lots_by_country.get("Indonesia", 0))

    st.subheader("The question, answered")
    st.write("**Can we predict a green coffee's Total Cup Points from facts known before it is cupped?** "
             f"{'A careful yes.' if gain > 0 else 'Not yet.'} On the test lots the typical miss is "
             f"{test_mae:.2f} cup points, against {baseline_test_mae:.2f} for always guessing the average, "
             f"so the model is {abs(gain):.2f} points {'better' if gain >= 0 else 'worse'} "
             f"({abs(gain) / baseline_test_mae:.0%}). R² is {r2:.2f}: origin, variety, processing, altitude, "
             f"moisture, defects and colour explain about {r2:.0%} of the differences between lots. "
             "The rest is in the cup.")

    st.subheader("What makes a green coffee score higher?")
    st.write(f"The model leans most on **{top_drivers[0]}**, **{top_drivers[1]}** and **{top_drivers[2]}**, "
             "the columns whose shuffling hurts the predictions most. This shows what the model uses, not "
             "what causes a high score. The ten cupping part scores are not used: they are the taster's own "
             "answers and add up to the total.")

    st.subheader("Limits")
    st.markdown(f"""
- **Imbalanced data.** {len(df):,} Arabica lots from the CQI reviews, below the brief's suggested few thousand rows. Coverage is uneven: {lots_by_country.index[0]} has {lots_by_country.iloc[0]} lots, Indonesia {indonesia_lots}.
- **Gaps.** {gap_moisture:.0%} of lots have no usable moisture and {gap_altitude:.0%} no altitude (a moisture of exactly 0.0 was most likely a missing value in disguise). The pipeline fills them from the training lots.
""")

    st.subheader("Would I use it?")
    st.write("Yes, to decide what to taste first, not to screen lots out. A typical miss of "
             f"{test_mae:.2f} points is enough to move a lot across the 80 line, so the model should rank "
             "lots, not pass or fail them.")

    st.divider()
    st.subheader("What's next")
    st.write("The idea that started this project is a **green bean identifier**: point a camera at a bean "
             "and see what is known about it. This project shows that a cup score can be predicted from "
             "the facts about a lot, but a camera needs something this data does not have: photos.")
    st.write("**To move closer to that goal I would need to go through labelling and recording thousands "
             "of green beans and save them to the database**: a photo of each bean, its origin, variety, "
             "processing, altitude, moisture, defects and colour, and its cup score. The CQI file has the "
             "facts and the scores, but no photos.")
    st.markdown(f"""
1. **Build the database.** Record and label thousands of green beans, with moisture and altitude measured and not left empty. This answers the two biggest limits above: too few lots and too many gaps.
2. **Cover more origins.** Add lots from origins the data barely has (Indonesia has {indonesia_lots}) and more Robusta, so the model is not Arabica-only.
3. **Teach the camera what it can see.** Train an image model on the photos to read colour, visible defects and size. Origin, altitude and moisture cannot be seen, so they come from the database or the supplier.
4. **Rerun the models on the bigger data.** Try the random forest and gradient boosting again, keep Huber only if it still wins, and check whether the error keeps falling.
5. **Build the identifier.** Upload a photo or point a live camera at a bean and see its information on screen, then try smart glasses such as the Ray-Ban Meta.
""")

elif page == P_THANKS:
    # the whole screen turns black on this slide only (the style is gone again on the next page)
    st.markdown("""
<style>
.stApp, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], .block-container, [data-testid="stHeader"],
[data-testid="stSidebar"], [data-testid="stSidebarContent"] { background: #000000 !important; }
[data-testid="stSidebar"] *, [data-testid="stHeader"] * { color: #d9d9d9 !important; }
div.thanks h1 { font-size: 2rem !important; font-weight: 500 !important; color: #ffffff !important; margin: 0 !important; }
div.thanks h3 { font-size: 1.1rem !important; font-weight: 400 !important; color: #cfcfcf !important;
                margin-top: 0.6rem !important; }
div.thanks p { font-size: 0.9rem !important; color: #8c8c8c !important; margin-top: 2.5rem !important; }
</style>
<div class="thanks" style="text-align:center; min-height:72vh; display:flex; flex-direction:column; justify-content:center;">
<h1>Thank you</h1>
<h3>Questions?</h3>
<p>Predicting the cupping score of green coffee with machine learning<br>
Project 2 · Machine Learning: From Data to Predictions · Ironhack</p>
</div>
""", unsafe_allow_html=True)

else:
    st.title("References")
    sources = load_sources()
    if not sources:
        st.warning("globe/data/sources.json was not found. Run python src/build_references_panel.py first.")
    else:
        by_type = {}
        for source in sources:
            by_type.setdefault(source.get("type", "other"), []).append(source)

        type_order = ["dataset", "paper", "image_set", "image set", "tool"]
        types = sorted(by_type, key=lambda t: type_order.index(t) if t in type_order else len(type_order))

        counts = ", ".join(f"{t.replace('_', ' ')} {len(by_type[t])}" for t in types)
        st.write(f"**{len(sources)} sources**, the same list as the References button on the globe: {counts}.")

        for t in types:
            with st.expander(f"{t.replace('_', ' ').capitalize()} ({len(by_type[t])})"):
                st.markdown("\n\n".join(source_line(s) for s in by_type[t]))
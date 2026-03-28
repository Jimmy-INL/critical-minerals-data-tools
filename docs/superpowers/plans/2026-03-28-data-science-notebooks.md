# Critical Minerals Data Science Notebooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create 8 Jupyter notebooks demonstrating data science exercises on the critical minerals dataset, incorporating open-source embedding models and Earth foundation models.

**Architecture:** Each notebook is standalone, reads data from `data/` CSVs or uses `cmm-data` loaders, installs its own ML dependencies inline via `%pip install`. Notebooks live in `notebooks/` at the repo root.

**Tech Stack:** pandas, plotly, networkx, scikit-learn, sentence-transformers (BGE/MiniLM embeddings), Lag-Llama/statsforecast (time-series FM), UMAP, faiss-cpu

---

## File Structure

```
notebooks/
  01_supply_chain_concentration_risk.ipynb   - HHI index + concentration dashboards
  02_trade_flow_network_analysis.ipynb       - Directed graph of mineral trade
  03_production_forecasting.ipynb            - Time-series forecasting with FMs
  04_mineral_deposit_clustering.ipynb        - Geospatial clustering with embeddings
  05_cross_source_data_fusion.ipynb          - BGS + USGS + trade unified scorecard
  06_nlp_research_corpus.ipynb               - Embedding + semantic search on OSTI docs
  07_anomaly_detection_production.ipynb      - Anomaly detection in production time-series
  08_geopolitical_scenario_modeling.ipynb    - "What-if" supply disruption scenarios
```

**Data files used (already in repo):**
- `data/bgs_data/bgs_critical_minerals_production.csv` (59K rows, columns: commodity, sub_commodity, statistic_type, country, country_iso2, country_iso3, year, quantity, units, yearbook_table, erml_commodity, erml_group, table_notes, figure_notes)
- `data/bgs_data/bgs_critical_minerals_trade.csv` (same schema, statistic_type = Imports/Exports)
- `data/usgs_mcs_data/2024/world.zip` (per-commodity CSVs like `mcs2024-lithi_world.csv`)
- `data/usgs_mcs_data/2024/salient.zip` (per-commodity salient stats)
- OSTI PDFs in `data/OSTI_retrieval/pdfs/` (if populated) or via OSTI API

---

### Task 1: Create notebooks directory and shared utility header

**Files:**
- Create: `notebooks/README.md`

- [ ] **Step 1: Create the notebooks directory**

```bash
mkdir -p notebooks
```

- [ ] **Step 2: Create a minimal README**

```markdown
# Critical Minerals Data Science Notebooks

Jupyter notebooks demonstrating data science exercises on the critical minerals dataset.

## Setup

```bash
uv pip install jupyter
jupyter notebook
```

## Notebooks

1. **Supply Chain Concentration Risk** - HHI index analysis
2. **Trade Flow Network Analysis** - Network graph of mineral trade
3. **Production Forecasting** - Time-series forecasting with foundation models
4. **Mineral Deposit Clustering** - Geospatial clustering with embeddings
5. **Cross-Source Data Fusion** - Unified mineral health scorecard
6. **NLP Research Corpus** - Semantic search with embeddings on OSTI docs
7. **Anomaly Detection** - Production anomaly detection
8. **Geopolitical Scenario Modeling** - Supply disruption "what-if" analysis
```

- [ ] **Step 3: Commit**

```bash
git add notebooks/README.md
git commit -m "feat: add notebooks directory with README"
```

---

### Task 2: Notebook 01 - Supply Chain Concentration Risk (HHI)

**Files:**
- Create: `notebooks/01_supply_chain_concentration_risk.ipynb`

This notebook computes the Herfindahl-Hirschman Index for each critical mineral, visualizes concentration risk over time, and ranks minerals by supply chain vulnerability.

- [ ] **Step 1: Create notebook with setup cell**

Cell 1 (code):
```python
%pip install pandas plotly kaleido -q

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

- [ ] **Step 2: Add data loading cell**

Cell 2 (markdown):
```markdown
## Load BGS Critical Minerals Production Data
59K rows of global mineral production from 1970-2023 across 100+ countries and 70+ commodities.
```

Cell 3 (code):
```python
df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
df = df[df["statistic_type"] == "Production"].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df = df.dropna(subset=["year", "quantity"])
df["year"] = df["year"].astype(int)
print(f"Production records: {len(df):,}")
print(f"Commodities: {df['commodity'].nunique()}")
print(f"Countries: {df['country'].nunique()}")
print(f"Year range: {df['year'].min()}-{df['year'].max()}")
df.head()
```

- [ ] **Step 3: Add HHI computation cell**

Cell 4 (markdown):
```markdown
## Herfindahl-Hirschman Index (HHI)
HHI = sum of squared market shares. Ranges from 0 (perfect competition) to 10,000 (monopoly).
- HHI < 1,500: Low concentration
- 1,500 < HHI < 2,500: Moderate concentration
- HHI > 2,500: High concentration
```

Cell 5 (code):
```python
def compute_hhi(group):
    """Compute HHI for a group of production records."""
    total = group["quantity"].sum()
    if total == 0:
        return 0
    shares = (group["quantity"] / total) * 100
    return (shares ** 2).sum()

# Compute HHI per commodity per year
hhi = (
    df.groupby(["commodity", "year"])
    .apply(compute_hhi, include_groups=False)
    .reset_index(name="hhi")
)
hhi.head()
```

- [ ] **Step 4: Add latest-year HHI ranking visualization**

Cell 6 (code):
```python
latest_year = hhi["year"].max()
hhi_latest = hhi[hhi["year"] == latest_year].sort_values("hhi", ascending=True)

fig = px.bar(
    hhi_latest,
    x="hhi",
    y="commodity",
    orientation="h",
    title=f"Supply Chain Concentration Risk ({latest_year}) - HHI by Commodity",
    labels={"hhi": "HHI (0=competitive, 10000=monopoly)", "commodity": ""},
    color="hhi",
    color_continuous_scale="RdYlGn_r",
    range_color=[0, 10000],
)
fig.add_vline(x=1500, line_dash="dash", line_color="orange", annotation_text="Moderate")
fig.add_vline(x=2500, line_dash="dash", line_color="red", annotation_text="High")
fig.update_layout(height=max(400, len(hhi_latest) * 22), showlegend=False)
fig.show()
```

- [ ] **Step 5: Add HHI over time for top concentrated minerals**

Cell 7 (code):
```python
# Top 10 most concentrated minerals in the latest year
top_concentrated = hhi_latest.nlargest(10, "hhi")["commodity"].tolist()
hhi_top = hhi[hhi["commodity"].isin(top_concentrated)]

fig = px.line(
    hhi_top,
    x="year",
    y="hhi",
    color="commodity",
    title="HHI Over Time - Top 10 Most Concentrated Minerals",
    labels={"hhi": "HHI", "year": "Year"},
)
fig.add_hline(y=2500, line_dash="dash", line_color="red", annotation_text="High concentration")
fig.add_hline(y=1500, line_dash="dash", line_color="orange", annotation_text="Moderate")
fig.update_layout(height=500)
fig.show()
```

- [ ] **Step 6: Add top producers per mineral heatmap**

Cell 8 (code):
```python
# For each top-concentrated mineral, show country shares in latest year
records = []
for commodity in top_concentrated[:6]:
    subset = df[(df["commodity"] == commodity) & (df["year"] == latest_year)]
    total = subset["quantity"].sum()
    if total > 0:
        subset = subset.copy()
        subset["share_pct"] = (subset["quantity"] / total) * 100
        top5 = subset.nlargest(5, "share_pct")
        for _, row in top5.iterrows():
            records.append({
                "commodity": commodity,
                "country": row["country"],
                "share_pct": row["share_pct"],
            })

shares_df = pd.DataFrame(records)
fig = px.bar(
    shares_df,
    x="share_pct",
    y="commodity",
    color="country",
    orientation="h",
    title=f"Top Producers Market Share ({latest_year}) - Most Concentrated Minerals",
    labels={"share_pct": "Market Share (%)", "commodity": ""},
    barmode="stack",
)
fig.update_layout(height=400)
fig.show()
```

- [ ] **Step 7: Add risk summary table**

Cell 9 (code):
```python
# Summary: commodity, HHI, top producer, top producer share, risk level
summary_records = []
for _, row in hhi_latest.iterrows():
    commodity = row["commodity"]
    subset = df[(df["commodity"] == commodity) & (df["year"] == latest_year)]
    total = subset["quantity"].sum()
    if total > 0:
        top = subset.nlargest(1, "quantity").iloc[0]
        summary_records.append({
            "Commodity": commodity,
            "HHI": round(row["hhi"]),
            "Top Producer": top["country"],
            "Top Producer Share (%)": round(top["quantity"] / total * 100, 1),
            "Risk Level": "HIGH" if row["hhi"] > 2500 else ("MODERATE" if row["hhi"] > 1500 else "LOW"),
        })

summary = pd.DataFrame(summary_records).sort_values("HHI", ascending=False)
summary.style.background_gradient(subset=["HHI"], cmap="RdYlGn_r")
```

- [ ] **Step 8: Commit**

```bash
git add notebooks/01_supply_chain_concentration_risk.ipynb
git commit -m "feat: add notebook 01 - supply chain concentration risk (HHI)"
```

---

### Task 3: Notebook 02 - Trade Flow Network Analysis

**Files:**
- Create: `notebooks/02_trade_flow_network_analysis.ipynb`

Builds a directed graph of mineral trade flows using BGS trade data, computes network metrics (betweenness centrality, PageRank), and identifies chokepoints.

- [ ] **Step 1: Create notebook with setup and data loading**

Cell 1 (code):
```python
%pip install pandas plotly networkx -q

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## Trade Flow Network Analysis
Build directed graphs of mineral trade (imports/exports) to identify chokepoints, hub countries, and vulnerable trade routes.
```

Cell 3 (code):
```python
trade = pd.read_csv(DATA_DIR / "bgs_critical_minerals_trade.csv")
trade["year"] = pd.to_numeric(trade["year"], errors="coerce")
trade["quantity"] = pd.to_numeric(trade["quantity"], errors="coerce")
trade = trade.dropna(subset=["year", "quantity"])
trade["year"] = trade["year"].astype(int)
print(f"Trade records: {len(trade):,}")
print(f"Commodities: {trade['commodity'].nunique()}")
print(f"Statistic types: {trade['statistic_type'].unique()}")
trade.head()
```

- [ ] **Step 2: Add network construction cell**

Cell 4 (markdown):
```markdown
## Build Trade Network
Since the trade data has imports/exports per country (not bilateral), we model each country's import as an edge from "World" to that country, and each export as an edge from that country to "World". This reveals hub-and-spoke patterns and dominant players.
```

Cell 5 (code):
```python
def build_trade_network(trade_df, commodity, year):
    """Build a directed trade graph for a commodity in a given year."""
    G = nx.DiGraph()
    subset = trade_df[(trade_df["commodity"] == commodity) & (trade_df["year"] == year)]

    exports = subset[subset["statistic_type"] == "Exports"]
    imports = subset[subset["statistic_type"] == "Imports"]

    for _, row in exports.iterrows():
        G.add_edge(row["country"], "Global Market", weight=row["quantity"],
                   country_iso3=row.get("country_iso3", ""))

    for _, row in imports.iterrows():
        G.add_edge("Global Market", row["country"], weight=row["quantity"],
                   country_iso3=row.get("country_iso3", ""))

    return G

# Pick a commodity with good trade data
latest_year = trade["year"].max()
commodity_counts = trade[trade["year"] == latest_year].groupby("commodity").size().sort_values(ascending=False)
print("Commodities with most trade records:")
print(commodity_counts.head(10))
```

- [ ] **Step 3: Add network metrics computation**

Cell 6 (code):
```python
# Build network for top commodity
top_commodity = commodity_counts.index[0]
G = build_trade_network(trade, top_commodity, latest_year)

print(f"\nTrade Network for '{top_commodity}' ({latest_year}):")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")

# Compute centrality metrics (exclude "Global Market" hub for meaningful metrics)
countries_only = [n for n in G.nodes() if n != "Global Market"]

# Degree centrality
degree = nx.degree_centrality(G)

# Betweenness centrality
betweenness = nx.betweenness_centrality(G, weight="weight")

# Export/import balance
balance = {}
for country in countries_only:
    exported = sum(d["weight"] for _, _, d in G.out_edges(country, data=True))
    imported = sum(d["weight"] for _, _, d in G.in_edges(country, data=True))
    balance[country] = {"exports": exported, "imports": imported,
                        "net": exported - imported,
                        "ratio": exported / imported if imported > 0 else float("inf")}

balance_df = pd.DataFrame(balance).T.sort_values("net", ascending=False)
balance_df.index.name = "country"
balance_df = balance_df.reset_index()
print(f"\nTop Exporters of {top_commodity}:")
balance_df.head(10)
```

- [ ] **Step 4: Add trade balance visualization**

Cell 7 (code):
```python
# Net trade balance bar chart
top_n = 20
top_traders = pd.concat([balance_df.head(top_n // 2), balance_df.tail(top_n // 2)])

fig = px.bar(
    top_traders,
    x="net",
    y="country",
    orientation="h",
    color="net",
    color_continuous_scale="RdBu",
    color_continuous_midpoint=0,
    title=f"Net Trade Balance: {top_commodity} ({latest_year})",
    labels={"net": "Net Exports (tonnes)", "country": ""},
)
fig.update_layout(height=500)
fig.show()
```

- [ ] **Step 5: Add multi-commodity network comparison**

Cell 8 (code):
```python
# Compare network structure across multiple commodities
commodities_to_compare = commodity_counts.head(6).index.tolist()
network_stats = []

for commodity in commodities_to_compare:
    G = build_trade_network(trade, commodity, latest_year)
    countries = [n for n in G.nodes() if n != "Global Market"]

    # Total trade volume
    total_exports = sum(d["weight"] for u, v, d in G.edges(data=True) if u != "Global Market")
    total_imports = sum(d["weight"] for u, v, d in G.edges(data=True) if v != "Global Market")

    # Concentration: share of top exporter
    export_volumes = {}
    for u, v, d in G.edges(data=True):
        if u != "Global Market":
            export_volumes[u] = export_volumes.get(u, 0) + d["weight"]

    top_share = max(export_volumes.values()) / total_exports * 100 if total_exports > 0 and export_volumes else 0

    network_stats.append({
        "commodity": commodity,
        "num_exporters": sum(1 for u, v in G.edges() if u != "Global Market"),
        "num_importers": sum(1 for u, v in G.edges() if v != "Global Market"),
        "total_exports": total_exports,
        "total_imports": total_imports,
        "top_exporter_share_pct": round(top_share, 1),
    })

stats_df = pd.DataFrame(network_stats)
fig = px.bar(
    stats_df,
    x="commodity",
    y="top_exporter_share_pct",
    color="top_exporter_share_pct",
    color_continuous_scale="RdYlGn_r",
    title=f"Export Concentration by Commodity ({latest_year})",
    labels={"top_exporter_share_pct": "Top Exporter Share (%)", "commodity": ""},
)
fig.update_layout(height=400)
fig.show()
```

- [ ] **Step 6: Commit**

```bash
git add notebooks/02_trade_flow_network_analysis.ipynb
git commit -m "feat: add notebook 02 - trade flow network analysis"
```

---

### Task 4: Notebook 03 - Production Forecasting with Foundation Models

**Files:**
- Create: `notebooks/03_production_forecasting.ipynb`

Uses statsforecast (Theta, AutoETS, AutoARIMA) and optionally Lag-Llama for time-series forecasting on BGS production data.

- [ ] **Step 1: Create notebook with setup**

Cell 1 (code):
```python
%pip install pandas plotly statsforecast datasetsforecast -q

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## Production Forecasting with Statistical & Foundation Models
Forecast critical mineral production using:
1. **Statistical baselines**: AutoARIMA, AutoETS, Theta (via statsforecast)
2. **Foundation model** (optional): Lag-Llama - a pretrained time-series transformer

We use 50+ years of BGS production data (1970-2023) to train and forecast.
```

- [ ] **Step 2: Add data preparation**

Cell 3 (code):
```python
df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
df = df[df["statistic_type"] == "Production"].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df = df.dropna(subset=["year", "quantity"])
df["year"] = df["year"].astype(int)

# Focus on key battery minerals and top producers
key_minerals = ["lithium minerals", "cobalt mine", "nickel mine", "graphite", "manganese ore"]
available = [m for m in key_minerals if m in df["commodity"].unique()]
print(f"Available key minerals: {available}")

# For each mineral, get top 3 producers by total recent production
forecast_series = []
for mineral in available:
    mineral_df = df[(df["commodity"] == mineral) & (df["year"] >= 2000)]
    top_countries = (
        mineral_df.groupby("country")["quantity"]
        .sum()
        .nlargest(3)
        .index.tolist()
    )
    for country in top_countries:
        series = df[(df["commodity"] == mineral) & (df["country"] == country)].copy()
        series = series.sort_values("year")
        if len(series) >= 10:  # Need enough history
            forecast_series.append({
                "mineral": mineral,
                "country": country,
                "data": series[["year", "quantity"]],
            })

print(f"\nForecast series prepared: {len(forecast_series)}")
for s in forecast_series:
    print(f"  {s['mineral']} - {s['country']}: {len(s['data'])} years")
```

- [ ] **Step 3: Add statsforecast modeling**

Cell 4 (code):
```python
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, AutoTheta

HORIZON = 5  # Forecast 5 years ahead

# Prepare data in statsforecast format (unique_id, ds, y)
sf_records = []
for i, s in enumerate(forecast_series):
    uid = f"{s['mineral']}|{s['country']}"
    for _, row in s["data"].iterrows():
        sf_records.append({
            "unique_id": uid,
            "ds": pd.Timestamp(year=int(row["year"]), month=1, day=1),
            "y": row["quantity"],
        })

sf_df = pd.DataFrame(sf_records)
print(f"StatsForecast input: {len(sf_df)} rows, {sf_df['unique_id'].nunique()} series")

sf = StatsForecast(
    models=[AutoARIMA(season_length=1), AutoETS(season_length=1), AutoTheta(season_length=1)],
    freq="YS",
    n_jobs=1,
)
forecasts = sf.forecast(df=sf_df, h=HORIZON)
forecasts = forecasts.reset_index()
forecasts.head()
```

- [ ] **Step 4: Add forecast visualization**

Cell 5 (code):
```python
# Plot forecasts for each series
for s in forecast_series[:6]:  # Limit to 6 plots
    uid = f"{s['mineral']}|{s['country']}"
    hist = sf_df[sf_df["unique_id"] == uid].copy()
    fcast = forecasts[forecasts["unique_id"] == uid].copy()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["ds"], y=hist["y"],
        mode="lines+markers", name="Historical",
        line=dict(color="blue"),
    ))

    for model_col, color in [("AutoARIMA", "red"), ("AutoETS", "green"), ("AutoTheta", "orange")]:
        if model_col in fcast.columns:
            fig.add_trace(go.Scatter(
                x=fcast["ds"], y=fcast[model_col],
                mode="lines+markers", name=model_col,
                line=dict(color=color, dash="dash"),
            ))

    fig.update_layout(
        title=f"Production Forecast: {s['mineral']} - {s['country']}",
        xaxis_title="Year", yaxis_title="Production (tonnes)",
        height=350,
    )
    fig.show()
```

- [ ] **Step 5: Add optional Lag-Llama cell**

Cell 6 (markdown):
```markdown
## (Optional) Lag-Llama Foundation Model Forecasting
Lag-Llama is a pretrained transformer for probabilistic time-series forecasting.
Uncomment and run the cell below if you have a GPU available. It will download the model (~350MB).
```

Cell 7 (code):
```python
# Uncomment to use Lag-Llama (requires GPU, ~350MB download)
# %pip install lag-llama gluonts torch -q
#
# import torch
# from gluonts.dataset.pandas import PandasDataset
# from lag_llama.gluon.estimator import LagLlamaEstimator
#
# # Prepare data for Lag-Llama
# for s in forecast_series[:3]:
#     uid = f"{s['mineral']}|{s['country']}"
#     series_data = sf_df[sf_df["unique_id"] == uid].set_index("ds")["y"]
#
#     dataset = PandasDataset({"target": series_data}, freq="YS")
#
#     estimator = LagLlamaEstimator(
#         prediction_length=HORIZON,
#         context_length=32,
#         input_size=1,
#         use_rope_scaling=False,
#     )
#
#     # Use pretrained checkpoint
#     predictor = estimator.train(dataset, num_batches_per_epoch=50, trainer_kwargs={"max_epochs": 5})
#
#     forecast_it = predictor.predict(dataset)
#     for forecast in forecast_it:
#         print(f"\n{uid}")
#         print(f"  Median forecast: {forecast.median}")
#         print(f"  Mean forecast: {forecast.mean}")
```

- [ ] **Step 6: Add model comparison summary**

Cell 8 (code):
```python
# Backtest: use last 3 years as test set
cv_results = sf.cross_validation(df=sf_df, h=3, step_size=1, n_windows=2)
cv_results = cv_results.reset_index()

# Compute MAPE per model
from datasetsforecast.losses import mape

model_cols = [c for c in cv_results.columns if c not in ["unique_id", "ds", "cutoff", "y"]]
mape_scores = {}
for model in model_cols:
    valid = cv_results[cv_results["y"] > 0]
    mape_scores[model] = np.mean(np.abs((valid["y"] - valid[model]) / valid["y"])) * 100

mape_df = pd.DataFrame(list(mape_scores.items()), columns=["Model", "MAPE (%)"]).sort_values("MAPE (%)")
fig = px.bar(mape_df, x="Model", y="MAPE (%)", title="Model Comparison (Cross-Validation MAPE)", color="MAPE (%)", color_continuous_scale="RdYlGn_r")
fig.show()
```

- [ ] **Step 7: Commit**

```bash
git add notebooks/03_production_forecasting.ipynb
git commit -m "feat: add notebook 03 - production forecasting with FMs"
```

---

### Task 5: Notebook 04 - Mineral Deposit Clustering with Embeddings

**Files:**
- Create: `notebooks/04_mineral_deposit_clustering.ipynb`

Uses sentence-transformers (BGE-large) to embed mineral deposit descriptions, then clusters with UMAP + HDBSCAN. Demonstrates using open-source embeddings on geoscience text.

- [ ] **Step 1: Create notebook with setup**

Cell 1 (code):
```python
%pip install pandas plotly sentence-transformers umap-learn hdbscan scikit-learn -q

import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## Mineral Deposit Clustering with Open-Source Embeddings
Use **BGE-large-en-v1.5** (BAAI) sentence embeddings to encode mineral production profiles, then cluster with UMAP + HDBSCAN to discover natural groupings of countries by their mineral production signatures.

### Models used:
- **BAAI/bge-large-en-v1.5** - Open-source embedding model (1024-dim, downloadable locally)
- **UMAP** - Dimensionality reduction
- **HDBSCAN** - Density-based clustering
```

- [ ] **Step 2: Add data preparation - country mineral profiles**

Cell 3 (code):
```python
df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
df = df[df["statistic_type"] == "Production"].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df = df.dropna(subset=["year", "quantity"])

# Use recent data (last 5 years available)
latest_year = int(df["year"].max())
recent = df[df["year"] >= latest_year - 4]

# Create a text profile for each country: what they produce and how much
country_profiles = []
for country, group in recent.groupby("country"):
    # Summarize production by commodity
    prod = group.groupby("commodity")["quantity"].sum().sort_values(ascending=False)
    if len(prod) < 2:
        continue  # Need at least 2 commodities for meaningful profile

    # Create natural language description
    top_minerals = []
    for mineral, qty in prod.head(10).items():
        top_minerals.append(f"{mineral}: {qty:,.0f} tonnes")

    profile_text = (
        f"{country} produces {len(prod)} minerals. "
        f"Top production: {'; '.join(top_minerals)}."
    )

    country_profiles.append({
        "country": country,
        "iso3": group["country_iso3"].iloc[0],
        "num_minerals": len(prod),
        "total_production": prod.sum(),
        "top_mineral": prod.index[0],
        "profile_text": profile_text,
    })

profiles_df = pd.DataFrame(country_profiles)
print(f"Country profiles: {len(profiles_df)}")
profiles_df.head()
```

- [ ] **Step 3: Add embedding generation**

Cell 4 (code):
```python
from sentence_transformers import SentenceTransformer

# Load BGE-large (downloads ~1.3GB on first run)
model = SentenceTransformer("BAAI/bge-large-en-v1.5")
print(f"Model loaded: {model.get_sentence_embedding_dimension()}-dim embeddings")

# Encode all country profiles
texts = profiles_df["profile_text"].tolist()
embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
print(f"Embeddings shape: {embeddings.shape}")
```

- [ ] **Step 4: Add UMAP + HDBSCAN clustering**

Cell 5 (code):
```python
import umap
import hdbscan

# Reduce to 2D with UMAP
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
coords_2d = reducer.fit_transform(embeddings)

# Cluster with HDBSCAN
clusterer = hdbscan.HDBSCAN(min_cluster_size=3, min_samples=2)
clusters = clusterer.fit_predict(embeddings)

profiles_df["umap_x"] = coords_2d[:, 0]
profiles_df["umap_y"] = coords_2d[:, 1]
profiles_df["cluster"] = clusters.astype(str)

n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
n_noise = (clusters == -1).sum()
print(f"Clusters found: {n_clusters}, Noise points: {n_noise}")
```

- [ ] **Step 5: Add interactive cluster visualization**

Cell 6 (code):
```python
fig = px.scatter(
    profiles_df,
    x="umap_x", y="umap_y",
    color="cluster",
    hover_name="country",
    hover_data=["top_mineral", "num_minerals", "total_production"],
    size="total_production",
    size_max=30,
    title="Country Mineral Production Profiles - Embedding Clusters (BGE-large)",
    labels={"umap_x": "UMAP-1", "umap_y": "UMAP-2"},
)
fig.update_layout(height=600, width=800)
fig.show()
```

- [ ] **Step 6: Add cluster interpretation**

Cell 7 (code):
```python
# Characterize each cluster
for cluster_id in sorted(profiles_df["cluster"].unique()):
    if cluster_id == "-1":
        continue
    cluster_countries = profiles_df[profiles_df["cluster"] == cluster_id]
    print(f"\n--- Cluster {cluster_id} ({len(cluster_countries)} countries) ---")
    print(f"Countries: {', '.join(cluster_countries['country'].tolist())}")

    # Most common top mineral
    top_minerals = cluster_countries["top_mineral"].value_counts()
    print(f"Dominant minerals: {dict(top_minerals.head(3))}")
    print(f"Avg minerals produced: {cluster_countries['num_minerals'].mean():.1f}")
```

- [ ] **Step 7: Add embedding similarity search**

Cell 8 (markdown):
```markdown
## Semantic Similarity Search
Find countries with similar mineral production profiles using cosine similarity on embeddings.
```

Cell 9 (code):
```python
from sklearn.metrics.pairwise import cosine_similarity

# Find countries most similar to a query country
query_country = "China"
query_idx = profiles_df[profiles_df["country"] == query_country].index[0]
query_embedding = embeddings[query_idx].reshape(1, -1)

similarities = cosine_similarity(query_embedding, embeddings)[0]
profiles_df["similarity_to_query"] = similarities

top_similar = profiles_df.nlargest(10, "similarity_to_query")[["country", "top_mineral", "num_minerals", "similarity_to_query"]]
print(f"Countries most similar to {query_country}:")
top_similar
```

- [ ] **Step 8: Commit**

```bash
git add notebooks/04_mineral_deposit_clustering.ipynb
git commit -m "feat: add notebook 04 - mineral deposit clustering with BGE embeddings"
```

---

### Task 6: Notebook 05 - Cross-Source Data Fusion

**Files:**
- Create: `notebooks/05_cross_source_data_fusion.ipynb`

Joins BGS production + BGS trade + USGS data to build a unified "mineral health scorecard" per country.

- [ ] **Step 1: Create notebook with setup and data loading**

Cell 1 (code):
```python
%pip install pandas plotly zipfile36 -q

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import zipfile
import io
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data")
BGS_DIR = DATA_DIR / "bgs_data"
USGS_DIR = DATA_DIR / "usgs_mcs_data" / "2024"
```

Cell 2 (markdown):
```markdown
## Cross-Source Data Fusion
Join BGS production + BGS trade + USGS world production data to build a unified mineral health scorecard.

**Data sources:**
- **BGS**: 59K production records + trade data (1970-2023)
- **USGS MCS 2024**: World production by commodity (ZIP archive)
```

Cell 3 (code):
```python
# Load BGS data
bgs_prod = pd.read_csv(BGS_DIR / "bgs_critical_minerals_production.csv")
bgs_trade = pd.read_csv(BGS_DIR / "bgs_critical_minerals_trade.csv")

for df_name, df_ref in [("bgs_prod", bgs_prod), ("bgs_trade", bgs_trade)]:
    df_ref["year"] = pd.to_numeric(df_ref["year"], errors="coerce")
    df_ref["quantity"] = pd.to_numeric(df_ref["quantity"], errors="coerce")

bgs_prod = bgs_prod[bgs_prod["statistic_type"] == "Production"]
print(f"BGS Production: {len(bgs_prod):,} rows")
print(f"BGS Trade: {len(bgs_trade):,} rows")
```

- [ ] **Step 2: Add USGS data loading from ZIP**

Cell 4 (code):
```python
# Load USGS world production data from ZIP
usgs_world_zip = USGS_DIR / "world.zip"
usgs_data = {}

with zipfile.ZipFile(usgs_world_zip, "r") as zf:
    csv_files = [f for f in zf.namelist() if f.endswith("_world.csv")]
    for csv_file in csv_files:
        # Extract commodity code from filename (e.g., mcs2024-lithi_world.csv -> lithi)
        name_part = csv_file.split("/")[-1]
        commodity_code = name_part.replace("mcs2024-", "").replace("MCS2024-", "").replace("_world.csv", "")

        with zf.open(csv_file) as f:
            try:
                usgs_df = pd.read_csv(io.TextIOWrapper(f))
                usgs_data[commodity_code] = usgs_df
            except Exception as e:
                pass

print(f"USGS commodities loaded: {len(usgs_data)}")
print(f"Examples: {list(usgs_data.keys())[:10]}")

# Show structure of one
sample_key = list(usgs_data.keys())[0]
print(f"\nSample ({sample_key}):")
usgs_data[sample_key].head()
```

- [ ] **Step 3: Add mineral health scorecard computation**

Cell 5 (code):
```python
latest_year = int(bgs_prod["year"].max())

# Compute per-country, per-commodity scorecard
key_minerals = ["lithium minerals", "cobalt mine", "nickel mine", "graphite", "copper mine",
                "manganese ore", "rare earth minerals", "tungsten", "vanadium"]
available_minerals = [m for m in key_minerals if m in bgs_prod["commodity"].unique()]

scorecard_records = []
for mineral in available_minerals:
    prod = bgs_prod[(bgs_prod["commodity"] == mineral) & (bgs_prod["year"] == latest_year)]
    trade = bgs_trade[(bgs_trade["commodity"] == mineral) & (bgs_trade["year"] == latest_year)]

    total_global = prod["quantity"].sum()

    for country in prod["country"].unique():
        country_prod = prod[prod["country"] == country]["quantity"].sum()
        country_exports = trade[(trade["country"] == country) & (trade["statistic_type"] == "Exports")]["quantity"].sum()
        country_imports = trade[(trade["country"] == country) & (trade["statistic_type"] == "Imports")]["quantity"].sum()

        # Production share
        prod_share = (country_prod / total_global * 100) if total_global > 0 else 0

        # Self-sufficiency ratio
        domestic_supply = country_prod + country_imports - country_exports
        self_sufficiency = (country_prod / domestic_supply * 100) if domestic_supply > 0 else 0

        scorecard_records.append({
            "mineral": mineral,
            "country": country,
            "iso3": prod[prod["country"] == country]["country_iso3"].iloc[0] if len(prod[prod["country"] == country]) > 0 else "",
            "production": country_prod,
            "exports": country_exports,
            "imports": country_imports,
            "global_share_pct": round(prod_share, 2),
            "self_sufficiency_pct": round(min(self_sufficiency, 200), 2),
        })

scorecard = pd.DataFrame(scorecard_records)
print(f"Scorecard entries: {len(scorecard):,}")
scorecard.sort_values("global_share_pct", ascending=False).head(10)
```

- [ ] **Step 4: Add visualizations**

Cell 6 (code):
```python
# Heatmap: country vs mineral production share
pivot = scorecard.pivot_table(index="country", columns="mineral", values="global_share_pct", aggfunc="sum")
# Keep only countries with at least one >5% share
significant = pivot[pivot.max(axis=1) >= 5].fillna(0)

fig = px.imshow(
    significant,
    title=f"Country Mineral Production Shares ({latest_year})",
    labels=dict(x="Mineral", y="Country", color="Share (%)"),
    color_continuous_scale="YlOrRd",
    aspect="auto",
)
fig.update_layout(height=max(400, len(significant) * 25))
fig.show()
```

Cell 7 (code):
```python
# Country vulnerability radar: pick top 5 producing countries
top_countries = scorecard.groupby("country")["production"].sum().nlargest(5).index.tolist()

fig = go.Figure()
for country in top_countries:
    country_data = scorecard[scorecard["country"] == country]
    minerals = country_data["mineral"].tolist()
    shares = country_data["global_share_pct"].tolist()

    fig.add_trace(go.Scatterpolar(
        r=shares + [shares[0]],
        theta=minerals + [minerals[0]],
        name=country,
        fill="toself",
        opacity=0.5,
    ))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 80])),
    title="Mineral Production Dominance Radar",
    height=500,
)
fig.show()
```

- [ ] **Step 5: Commit**

```bash
git add notebooks/05_cross_source_data_fusion.ipynb
git commit -m "feat: add notebook 05 - cross-source data fusion scorecard"
```

---

### Task 7: Notebook 06 - NLP Research Corpus with Embeddings

**Files:**
- Create: `notebooks/06_nlp_research_corpus.ipynb`

Embeds OSTI document metadata (or BGS commodity descriptions as fallback) with sentence-transformers, builds a FAISS index for semantic search, and demonstrates RAG-like retrieval.

- [ ] **Step 1: Create notebook with setup**

Cell 1 (code):
```python
%pip install pandas plotly sentence-transformers faiss-cpu umap-learn -q

import pandas as pd
import numpy as np
import plotly.express as px
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## NLP on Critical Minerals Research Corpus
Use **all-MiniLM-L6-v2** embeddings + **FAISS** vector index to build a semantic search engine over critical minerals data.

### Approach:
1. Create a text corpus from BGS production records (commodity + country descriptions)
2. Embed with **sentence-transformers** (all-MiniLM-L6-v2, 384-dim, fast)
3. Index with **FAISS** for efficient nearest-neighbor search
4. Demonstrate semantic queries
```

- [ ] **Step 2: Add corpus creation from BGS data**

Cell 3 (code):
```python
df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
df = df[df["statistic_type"] == "Production"].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df = df.dropna(subset=["year", "quantity"])
latest_year = int(df["year"].max())

# Create document corpus: one document per country-commodity pair with production summary
docs = []
for (commodity, country), group in df.groupby(["commodity", "country"]):
    group = group.sort_values("year")
    years = group["year"].astype(int)
    quantities = group["quantity"]
    latest_qty = group[group["year"] == latest_year]["quantity"].sum()

    units = group["units"].iloc[0] if "units" in group.columns else "tonnes"
    notes = group["table_notes"].iloc[0] if pd.notna(group["table_notes"].iloc[0]) else ""

    text = (
        f"{country} produces {commodity}. "
        f"Production history spans {int(years.min())}-{int(years.max())} ({len(group)} years of data). "
        f"Latest production ({latest_year}): {latest_qty:,.0f} {units}. "
        f"Peak production: {quantities.max():,.0f} {units} in {int(years.iloc[quantities.argmax()])}. "
        f"Average production: {quantities.mean():,.0f} {units}."
    )
    if notes:
        text += f" Notes: {notes[:200]}"

    docs.append({
        "commodity": commodity,
        "country": country,
        "iso3": group["country_iso3"].iloc[0],
        "latest_production": latest_qty,
        "text": text,
    })

corpus_df = pd.DataFrame(docs)
print(f"Corpus size: {len(corpus_df)} documents")
print(f"Commodities: {corpus_df['commodity'].nunique()}")
print(f"Countries: {corpus_df['country'].nunique()}")
print(f"\nSample document:\n{corpus_df['text'].iloc[0]}")
```

- [ ] **Step 3: Add embedding generation**

Cell 4 (code):
```python
# Use MiniLM for speed (384-dim, ~80MB)
model = SentenceTransformer("all-MiniLM-L6-v2")
print(f"Model: all-MiniLM-L6-v2 ({model.get_sentence_embedding_dimension()}-dim)")

texts = corpus_df["text"].tolist()
embeddings = model.encode(texts, show_progress_bar=True, batch_size=64)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)  # L2 normalize
print(f"Embeddings shape: {embeddings.shape}")
```

- [ ] **Step 4: Add FAISS index and semantic search**

Cell 5 (code):
```python
# Build FAISS index
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim)  # Inner product (cosine similarity since normalized)
index.add(embeddings.astype(np.float32))
print(f"FAISS index: {index.ntotal} vectors, {dim}-dim")

def semantic_search(query, top_k=10):
    """Search the corpus using semantic similarity."""
    query_emb = model.encode([query])
    query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
    scores, indices = index.search(query_emb.astype(np.float32), top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        row = corpus_df.iloc[idx]
        results.append({
            "score": round(float(score), 4),
            "commodity": row["commodity"],
            "country": row["country"],
            "text": row["text"][:150] + "...",
        })
    return pd.DataFrame(results)

# Demo searches
queries = [
    "Which countries produce lithium for batteries?",
    "Rare earth element production in Africa",
    "Cobalt mining in Democratic Republic of Congo",
    "Platinum group metals supply chain",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    results = semantic_search(query, top_k=5)
    for _, r in results.iterrows():
        print(f"  [{r['score']:.3f}] {r['country']} - {r['commodity']}")
```

- [ ] **Step 5: Add embedding space visualization**

Cell 6 (code):
```python
import umap

# Reduce embeddings to 2D for visualization
reducer = umap.UMAP(n_components=2, random_state=42, n_neighbors=30)
coords = reducer.fit_transform(embeddings)

corpus_df["umap_x"] = coords[:, 0]
corpus_df["umap_y"] = coords[:, 1]

fig = px.scatter(
    corpus_df,
    x="umap_x", y="umap_y",
    color="commodity",
    hover_name="country",
    hover_data=["commodity", "latest_production"],
    title="Embedding Space: Critical Minerals Production Documents",
    labels={"umap_x": "UMAP-1", "umap_y": "UMAP-2"},
    opacity=0.6,
)
fig.update_layout(height=600, width=900)
fig.show()
```

- [ ] **Step 6: Commit**

```bash
git add notebooks/06_nlp_research_corpus.ipynb
git commit -m "feat: add notebook 06 - NLP research corpus with embeddings + FAISS"
```

---

### Task 8: Notebook 07 - Anomaly Detection in Production

**Files:**
- Create: `notebooks/07_anomaly_detection_production.ipynb`

Detects anomalies (sudden drops/spikes) in production time-series using statistical methods and isolation forest.

- [ ] **Step 1: Create notebook with setup and data loading**

Cell 1 (code):
```python
%pip install pandas plotly scikit-learn -q

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## Anomaly Detection in Mineral Production
Detect sudden production drops/spikes that may indicate:
- Sanctions or trade restrictions
- Mine collapses or natural disasters
- Policy changes (nationalization, export bans)
- Market disruptions

**Methods:**
1. Z-score on year-over-year changes
2. Isolation Forest (sklearn)
```

Cell 3 (code):
```python
df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
df = df[df["statistic_type"] == "Production"].copy()
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df = df.dropna(subset=["year", "quantity"])
df["year"] = df["year"].astype(int)
df = df.sort_values(["commodity", "country", "year"])

# Compute year-over-year change
df["prev_quantity"] = df.groupby(["commodity", "country"])["quantity"].shift(1)
df["yoy_change"] = (df["quantity"] - df["prev_quantity"]) / df["prev_quantity"]
df["yoy_change"] = df["yoy_change"].replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=["yoy_change"])

print(f"Records with YoY change: {len(df):,}")
```

- [ ] **Step 2: Add Z-score anomaly detection**

Cell 4 (code):
```python
# Z-score method: flag changes > 2 standard deviations
df["yoy_zscore"] = df.groupby(["commodity", "country"])["yoy_change"].transform(
    lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
)
df["is_anomaly_zscore"] = df["yoy_zscore"].abs() > 2.5

anomalies_z = df[df["is_anomaly_zscore"]].copy()
print(f"Z-score anomalies: {len(anomalies_z):,}")

# Top anomalies by magnitude
top_anomalies = anomalies_z.nlargest(20, "yoy_zscore", "all")[
    ["commodity", "country", "year", "quantity", "prev_quantity", "yoy_change", "yoy_zscore"]
]
top_anomalies["yoy_change_pct"] = (top_anomalies["yoy_change"] * 100).round(1)
top_anomalies
```

- [ ] **Step 3: Add Isolation Forest**

Cell 5 (code):
```python
# Isolation Forest on production features
feature_records = []
for (commodity, country), group in df.groupby(["commodity", "country"]):
    if len(group) < 5:
        continue
    feature_records.append({
        "commodity": commodity,
        "country": country,
        "mean_yoy": group["yoy_change"].mean(),
        "std_yoy": group["yoy_change"].std(),
        "max_drop": group["yoy_change"].min(),
        "max_spike": group["yoy_change"].max(),
        "volatility": group["quantity"].std() / group["quantity"].mean() if group["quantity"].mean() > 0 else 0,
        "num_years": len(group),
    })

features_df = pd.DataFrame(feature_records)
feature_cols = ["mean_yoy", "std_yoy", "max_drop", "max_spike", "volatility"]

iso_forest = IsolationForest(contamination=0.1, random_state=42)
features_df["anomaly_score"] = iso_forest.fit_predict(features_df[feature_cols].fillna(0))
features_df["is_anomaly_if"] = features_df["anomaly_score"] == -1

anomalous_series = features_df[features_df["is_anomaly_if"]].sort_values("volatility", ascending=False)
print(f"Anomalous production series (Isolation Forest): {len(anomalous_series)}")
anomalous_series[["commodity", "country", "volatility", "max_drop", "max_spike"]].head(15)
```

- [ ] **Step 4: Add anomaly visualizations**

Cell 6 (code):
```python
# Plot top anomalous series with anomaly points highlighted
for _, row in anomalous_series.head(6).iterrows():
    series = df[(df["commodity"] == row["commodity"]) & (df["country"] == row["country"])].sort_values("year")
    anomaly_points = series[series["is_anomaly_zscore"]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series["year"], y=series["quantity"],
        mode="lines", name="Production",
        line=dict(color="blue"),
    ))
    fig.add_trace(go.Scatter(
        x=anomaly_points["year"], y=anomaly_points["quantity"],
        mode="markers", name="Anomaly",
        marker=dict(color="red", size=12, symbol="x"),
    ))
    fig.update_layout(
        title=f"Anomalies: {row['commodity']} - {row['country']} (volatility={row['volatility']:.2f})",
        xaxis_title="Year", yaxis_title="Production",
        height=300,
    )
    fig.show()
```

Cell 7 (code):
```python
# Anomaly heatmap: year vs commodity (count of country-level anomalies)
anomaly_counts = anomalies_z.groupby(["commodity", "year"]).size().reset_index(name="num_anomalies")
pivot = anomaly_counts.pivot_table(index="commodity", columns="year", values="num_anomalies", fill_value=0)

fig = px.imshow(
    pivot,
    title="Production Anomalies Over Time (Count per Commodity per Year)",
    labels=dict(x="Year", y="Commodity", color="# Anomalies"),
    color_continuous_scale="YlOrRd",
    aspect="auto",
)
fig.update_layout(height=max(400, len(pivot) * 20))
fig.show()
```

- [ ] **Step 5: Commit**

```bash
git add notebooks/07_anomaly_detection_production.ipynb
git commit -m "feat: add notebook 07 - anomaly detection in production data"
```

---

### Task 9: Notebook 08 - Geopolitical Scenario Modeling

**Files:**
- Create: `notebooks/08_geopolitical_scenario_modeling.ipynb`

Models "what-if" supply disruption scenarios (e.g., China restricts rare earth exports by 50%) and identifies alternative suppliers.

- [ ] **Step 1: Create notebook with setup**

Cell 1 (code):
```python
%pip install pandas plotly networkx -q

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("../data/bgs_data")
```

Cell 2 (markdown):
```markdown
## Geopolitical Scenario Modeling
Model supply disruption scenarios and identify alternative suppliers.

### Scenarios:
1. **China restricts rare earth exports by 50%**
2. **DRC cobalt production drops by 30%** (conflict/instability)
3. **Russia sanctions cut nickel supply**
4. **Custom scenario builder**
```

- [ ] **Step 2: Add data loading and baseline computation**

Cell 3 (code):
```python
prod_df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_production.csv")
trade_df = pd.read_csv(DATA_DIR / "bgs_critical_minerals_trade.csv")

for frame in [prod_df, trade_df]:
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["quantity"] = pd.to_numeric(frame["quantity"], errors="coerce")

prod_df = prod_df[(prod_df["statistic_type"] == "Production") & prod_df["quantity"].notna()].copy()
latest_year = int(prod_df["year"].max())

def get_baseline(commodity):
    """Get baseline production and trade for a commodity in the latest year."""
    prod = prod_df[(prod_df["commodity"] == commodity) & (prod_df["year"] == latest_year)]
    trade = trade_df[(trade_df["commodity"] == commodity) & (trade_df["year"] == latest_year)]

    production = prod.groupby("country")["quantity"].sum().to_dict()
    exports = trade[trade["statistic_type"] == "Exports"].groupby("country")["quantity"].sum().to_dict()
    imports = trade[trade["statistic_type"] == "Imports"].groupby("country")["quantity"].sum().to_dict()

    return {"production": production, "exports": exports, "imports": imports,
            "total_production": sum(production.values())}

# Test baseline
baseline = get_baseline("rare earth minerals")
print(f"Rare Earth baseline ({latest_year}):")
print(f"  Total production: {baseline['total_production']:,.0f}")
print(f"  Top producers: {dict(sorted(baseline['production'].items(), key=lambda x: -x[1])[:5])}")
```

- [ ] **Step 3: Add scenario simulation engine**

Cell 4 (code):
```python
def simulate_disruption(commodity, disruptions, ramp_up_factor=0.5):
    """
    Simulate a supply disruption scenario.

    Args:
        commodity: Mineral commodity name
        disruptions: dict of {country: reduction_fraction} (e.g., {"China": 0.5} = 50% cut)
        ramp_up_factor: How much other producers can increase (0-1)

    Returns:
        DataFrame with scenario results
    """
    baseline = get_baseline(commodity)
    total_before = baseline["total_production"]

    results = []
    total_lost = 0

    for country, production in baseline["production"].items():
        reduction = disruptions.get(country, 0)
        lost = production * reduction
        total_lost += lost

        results.append({
            "country": country,
            "baseline_production": production,
            "reduction_pct": reduction * 100,
            "production_lost": lost,
            "scenario_production": production - lost,
        })

    results_df = pd.DataFrame(results).sort_values("baseline_production", ascending=False)

    # Estimate ramp-up from non-disrupted producers
    non_disrupted = results_df[results_df["reduction_pct"] == 0].copy()
    ramp_up_capacity = non_disrupted["baseline_production"].sum() * ramp_up_factor
    actual_ramp_up = min(ramp_up_capacity, total_lost)

    # Distribute ramp-up proportionally
    if non_disrupted["baseline_production"].sum() > 0:
        non_disrupted["ramp_up"] = (
            non_disrupted["baseline_production"] / non_disrupted["baseline_production"].sum() * actual_ramp_up
        )
        results_df = results_df.merge(
            non_disrupted[["country", "ramp_up"]], on="country", how="left"
        )
        results_df["ramp_up"] = results_df["ramp_up"].fillna(0)
        results_df["scenario_production"] += results_df["ramp_up"]
    else:
        results_df["ramp_up"] = 0

    total_after = results_df["scenario_production"].sum()

    summary = {
        "commodity": commodity,
        "total_before": total_before,
        "total_lost": total_lost,
        "total_ramp_up": actual_ramp_up,
        "total_after": total_after,
        "net_deficit": total_before - total_after,
        "deficit_pct": (total_before - total_after) / total_before * 100 if total_before > 0 else 0,
    }

    return results_df, summary

# Scenario 1: China cuts rare earth by 50%
results1, summary1 = simulate_disruption("rare earth minerals", {"China": 0.5})
print("Scenario: China -50% Rare Earth Production")
print(f"  Before: {summary1['total_before']:,.0f}")
print(f"  Lost: {summary1['total_lost']:,.0f}")
print(f"  Ramp-up: {summary1['total_ramp_up']:,.0f}")
print(f"  After: {summary1['total_after']:,.0f}")
print(f"  Net deficit: {summary1['net_deficit']:,.0f} ({summary1['deficit_pct']:.1f}%)")
```

- [ ] **Step 4: Add scenario visualizations**

Cell 5 (code):
```python
scenarios = [
    ("rare earth minerals", {"China": 0.5}, "China -50% Rare Earths"),
    ("cobalt mine", {"Congo (Kinshasa)": 0.3}, "DRC -30% Cobalt"),
    ("nickel mine", {"Russia": 1.0, "Russian Federation": 1.0}, "Russia -100% Nickel (Sanctions)"),
    ("lithium minerals", {"Australia": 0.4, "Chile": 0.4}, "Australia & Chile -40% Lithium"),
]

fig = make_subplots(rows=2, cols=2, subplot_titles=[s[2] for s in scenarios])

for i, (commodity, disruptions, title) in enumerate(scenarios):
    results, summary = simulate_disruption(commodity, disruptions)
    top = results.nlargest(8, "baseline_production")

    row, col = divmod(i, 2)
    fig.add_trace(go.Bar(
        x=top["country"], y=top["baseline_production"],
        name="Baseline", marker_color="steelblue",
        showlegend=(i == 0),
    ), row=row+1, col=col+1)
    fig.add_trace(go.Bar(
        x=top["country"], y=top["scenario_production"],
        name="After Disruption", marker_color="tomato",
        showlegend=(i == 0),
    ), row=row+1, col=col+1)

fig.update_layout(
    title="Geopolitical Scenario Comparison",
    height=700, barmode="group",
)
fig.show()
```

- [ ] **Step 5: Add alternative supplier identification**

Cell 6 (code):
```python
def find_alternative_suppliers(commodity, disrupted_country, lookback_years=10):
    """Find countries that could ramp up production based on historical capacity."""
    recent = prod_df[
        (prod_df["commodity"] == commodity) &
        (prod_df["year"] >= latest_year - lookback_years) &
        (prod_df["country"] != disrupted_country)
    ]

    alternatives = []
    for country, group in recent.groupby("country"):
        peak = group["quantity"].max()
        current = group[group["year"] == latest_year]["quantity"].sum()
        spare_capacity = max(0, peak - current)

        # Growth trend
        if len(group) >= 3:
            years = group["year"].values
            qtys = group["quantity"].values
            trend = np.polyfit(years, qtys, 1)[0] if len(years) > 1 else 0
        else:
            trend = 0

        alternatives.append({
            "country": country,
            "current_production": current,
            "peak_production": peak,
            "spare_capacity": spare_capacity,
            "growth_trend": trend,
            "ramp_up_potential": spare_capacity + max(0, trend * 3),  # 3-year growth
        })

    return pd.DataFrame(alternatives).sort_values("ramp_up_potential", ascending=False)

# Find alternatives for rare earths if China disrupted
alts = find_alternative_suppliers("rare earth minerals", "China")
print("Alternative Rare Earth Suppliers (if China disrupted):")
alts.head(10)
```

Cell 7 (code):
```python
# Visualize alternative suppliers
top_alts = alts.head(10)
fig = px.bar(
    top_alts,
    x="country",
    y=["current_production", "spare_capacity"],
    title="Rare Earth Alternative Suppliers - Current Production vs Spare Capacity",
    barmode="stack",
    labels={"value": "Production (tonnes)", "country": ""},
    color_discrete_map={"current_production": "steelblue", "spare_capacity": "lightgreen"},
)
fig.update_layout(height=400)
fig.show()
```

- [ ] **Step 6: Add interactive scenario builder**

Cell 8 (markdown):
```markdown
## Custom Scenario Builder
Modify the parameters below to model your own disruption scenario.
```

Cell 9 (code):
```python
# === CUSTOMIZE YOUR SCENARIO HERE ===
COMMODITY = "lithium minerals"     # Change to any commodity
DISRUPTIONS = {                     # country: fraction_reduction (0-1)
    "Australia": 0.3,               # 30% reduction
    "Chile": 0.2,                   # 20% reduction
}
RAMP_UP_FACTOR = 0.3               # How much others can increase (0-1)
# =====================================

results, summary = simulate_disruption(COMMODITY, DISRUPTIONS, RAMP_UP_FACTOR)
print(f"Custom Scenario: {COMMODITY}")
print(f"  Disruptions: {DISRUPTIONS}")
print(f"  Total before: {summary['total_before']:,.0f}")
print(f"  Net deficit: {summary['net_deficit']:,.0f} ({summary['deficit_pct']:.1f}%)")
print(f"\nTop producers after disruption:")
results.nlargest(10, "scenario_production")[["country", "baseline_production", "scenario_production", "ramp_up"]]
```

- [ ] **Step 7: Commit**

```bash
git add notebooks/08_geopolitical_scenario_modeling.ipynb
git commit -m "feat: add notebook 08 - geopolitical scenario modeling"
```

---

### Task 10: Final review and integration commit

- [ ] **Step 1: Verify all notebooks are present**

```bash
ls -la notebooks/*.ipynb
```

Expected: 8 notebook files (01 through 08).

- [ ] **Step 2: Run a quick sanity check on notebook JSON validity**

```bash
python -c "
import json
from pathlib import Path
for nb in sorted(Path('notebooks').glob('*.ipynb')):
    data = json.loads(nb.read_text())
    n_cells = len(data['cells'])
    print(f'{nb.name}: {n_cells} cells, valid JSON')
"
```

- [ ] **Step 3: Commit the README update with complete list**

```bash
git add notebooks/
git commit -m "feat: complete 8 data science notebooks for critical minerals analysis"
```

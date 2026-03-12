# Codex Build Prompt — Streamlit App for Implied Correlation of a Custom Equity Portfolio / Index

## Role and goal

You are a senior Python quant-dev engineer. Build a production-quality **Streamlit** application that computes and visualizes **implied correlation** for either:

1. a **standard equity index** represented by a user-uploaded constituent file, or  
2. a **custom portfolio / basket** defined by the user in the same format.

The end user is a trader or risk analyst using the tool to support **dispersion trading decisions** between **single names and an index/basket**.

The app must be practical, well-structured, easy to test locally, and easy to migrate later from a mock CSV data source to a real cloud data source.

---

## Business context

The tool should help answer questions like:

- Is **index volatility** rich or cheap relative to the **weighted single-name volatilities**?
- What **implied correlation** is the market currently pricing for this index or custom basket?
- How has that **implied correlation evolved historically** over the chosen lookback window?
- Are there names whose vols are disproportionately influencing the portfolio-level result?
- For dispersion trading, is the setup pointing more toward **short index vol / long single-name vol** or the opposite?

The app is meant to start with a **simple, robust MVP** and then be extensible.

---

## Theory to implement

### 1) Core variance identity

For an index or basket with weights \(w_i\), constituent volatilities \(\sigma_i\), and pairwise correlations \(\rho_{ij}\), the basket variance is:

\[
\sigma_I^2 = \sum_i w_i^2 \sigma_i^2 + \sum_{i\neq j} w_i w_j \sigma_i \sigma_j \rho_{ij}
\]

Where:

- \(\sigma_I\) = index / basket implied volatility
- \(w_i\) = constituent weights
- \(\sigma_i\) = constituent implied volatilities
- \(\rho_{ij}\) = pairwise correlations

### 2) Constant-correlation approximation

For a practical implied-correlation monitor, assume a **single common implied correlation** \(\rho_{imp}\) across all constituent pairs. Then:

\[
\sigma_I^2 = \sum_i w_i^2 \sigma_i^2 + \rho_{imp} \sum_{i\neq j} w_i w_j \sigma_i \sigma_j
\]

Rearrange to obtain:

\[
\rho_{imp} = \frac{\sigma_I^2 - \sum_i w_i^2 \sigma_i^2}{\sum_{i\neq j} w_i w_j \sigma_i \sigma_j}
\]

This is the **main formula** the app must use.

### 3) Approximate shortcut

Also compute and expose the common shortcut approximation:

\[
\rho_{imp}^{approx} \approx \frac{\sigma_I^2}{\sum_i w_i \sigma_i^2}
\]

This is only an approximation. The app must label it clearly as such, and default to the **full constant-correlation formula** above.

### 4) Realized correlation proxy

Also compute a **realized correlation proxy** from historical price returns for comparison.

Suggested implementation:

- Pull price history for index and constituents.
- Compute log returns or simple returns (make this configurable; default to log returns).
- Compute rolling realized covariance matrix of constituents.
- Compute realized basket variance from weights and covariance matrix.
- Infer a realized average correlation using the same constant-correlation approximation:

\[
\rho_{realized,t} = \frac{\sigma_{basket,realized,t}^2 - \sum_i w_i^2 \sigma_{i,realized,t}^2}{\sum_{i\neq j} w_i w_j \sigma_{i,realized,t} \sigma_{j,realized,t}}
\]

At MVP stage, this can be a rolling realized correlation over a user-set window such as 20 / 60 / 120 trading days.

### 5) Dispersion-trading interpretation

The app should not give financial advice, but it should display descriptive diagnostics such as:

- **Index vol vs weighted constituent vol**
- **Current implied correlation percentile** over the lookback period
- **Implied minus realized correlation spread**
- **Top weighted contributors** to single-name variance
- A plain-English interpretation panel, for example:
  - "High implied correlation means the market is pricing stronger co-movement across constituents."
  - "If implied correlation is rich versus history while index vol is elevated relative to constituents, that may be consistent with a short-correlation / long-dispersion setup, subject to full risk analysis."

Do **not** hardcode a simplistic trade recommendation. Provide diagnostics, not advice.

---

## Reference material to respect

Use the attached trading-volatility chapter as the main theory anchor for:

- index variance being bounded by weighted constituent variance,
- implied correlation derived from index and single-name volatilities,
- dispersion trading as index vol vs single-stock vol,
- the distinction between theta-weighted and vega-weighted dispersion,
- the fact that dispersion is not identical to a pure correlation swap exposure.

Also rely on official library docs for implementation details when needed.

---

## Data layer requirements

### Real production interface to preserve

The future production system uses a Python class with methods like:

```python
cache.get_vol(ticker, delta, tenor, start_date, end_date)
cache.px(ticker, start_date, end_date)
```

For this project, **do not connect to the real database**. Instead, design the code so the mock data source implements the same logical interface.

### Required abstraction

Create a clean data access layer, e.g.:

```python
class DataProvider(Protocol):
    def get_vol(self, ticker: str, delta: int, tenor: str, start_date: date, end_date: date) -> pd.DataFrame: ...
    def px(self, ticker: str, start_date: date, end_date: date) -> pd.DataFrame: ...
```

Then implement:

1. `MockCsvDataProvider` for local CSV files
2. `CloudDataProvider` placeholder / stub for future use

The app should only depend on the abstract provider, not on the concrete source.

### Mock data scope

Start with only:

- **delta = 50**
- **tenor = 1Y**

Assume a single volatility time series per ticker corresponding to 50-delta, 1-year implied volatility.

### Mock data storage format

Use CSV files stored under a local `data/` directory.

Recommended structure:

```text
project_root/
  app.py
  src/
    data/
    analytics/
    charts/
    ui/
    utils/
  data/
    vols/
      SX7P Index_vol_50d_1y.csv
      SAN SQ Equity_vol_50d_1y.csv
      BNP FP Equity_vol_50d_1y.csv
      ...
    prices/
      SX7P Index_px.csv
      SAN SQ Equity_px.csv
      BNP FP Equity_px.csv
      ...
    samples/
      sx7p_members.csv
```

### CSV format conventions

#### Vol CSV

```csv
date,ticker,delta,tenor,implied_vol
2024-01-02,SX7P Index,50,1Y,0.245
2024-01-03,SX7P Index,50,1Y,0.247
```

#### Price CSV

```csv
date,ticker,close
2024-01-02,SX7P Index,132.45
2024-01-03,SX7P Index,131.88
```

Use implied vol in **decimal format** internally, not vol points. The UI can display percentages.

---

## Input file format for basket constituents

The app must accept a CSV upload from the user.

### Expected format

- **First row**: the index / basket ticker itself
- **Remaining rows**: the constituent names
- **Column 1**: ticker
- **Column 2**: weight

Example:

```csv
ticker,weight
SX7P Index,100
SAN SQ Equity,12.3
BNP FP Equity,11.1
ACA FP Equity,8.4
DBK GY Equity,7.8
...
```

### Important parsing rule

Interpret the uploaded CSV as follows:

- Row 1 is the **basket / index ticker**.
- Rows 2 onward are the **members**.
- The basket row weight is informational and can be ignored in the analytics.
- Constituent weights should sum to approximately 100.

The app must validate:

- file has at least 3 rows,
- required columns exist,
- constituent weights are numeric,
- constituent weights sum to 100 ± tolerance,
- there are no duplicate constituent tickers,
- the basket ticker is not duplicated among members.

If validation fails, show clear Streamlit errors.

---

## App workflow

### Default workflow

1. User uploads the constituent CSV.
2. App parses the basket ticker and members.
3. Default lookback = **1 year**, adjustable in the UI.
4. App fetches:
   - basket implied vol time series,
   - constituent implied vol time series,
   - basket price series,
   - constituent price series.
5. App aligns data to a common date index.
6. App computes:
   - current implied correlation,
   - historical implied correlation time series,
   - realized correlation time series,
   - index vol vs weighted single-name vol diagnostics,
   - contribution analysis.
7. App renders interactive Plotly charts and summary tables.

### User controls

At minimum include:

- uploaded basket CSV
- lookback start / end dates, with default = latest 1 year
- rolling realized-correlation window (20 / 60 / 120, default 60)
- return type selector: log or simple
- option to choose full formula vs approximation for display comparison
- checkbox to normalize weights if user file sums to 1 instead of 100
- checkbox to winsorize / drop missing dates conservatively

Future-ready but optional:

- delta selector
- tenor selector
- ability to compare multiple baskets
- ability to exclude constituents with missing data

---

## Required analytics

### A. Current snapshot metrics

Display metric cards for the latest common date:

- Basket ticker
- Number of valid constituents used
- Basket implied vol (current)
- Weighted average constituent implied vol
- Weighted average constituent variance
- Current implied correlation (full formula)
- Current implied correlation (approximation)
- Current rolling realized correlation
- Implied minus realized correlation spread
- Current percentile rank of implied correlation within selected lookback

### B. Historical time series

Compute daily historical series for:

- basket implied vol
- weighted average constituent implied vol
- weighted average constituent variance
- implied correlation (full formula)
- implied correlation approximation
- rolling realized correlation
- implied minus realized spread

### C. Contribution analysis

For latest date and optionally historical average, compute:

1. constituent contribution to weighted single-name variance term:
   \[
   w_i^2 \sigma_i^2
   \]
2. constituent contribution to weighted constituent vol basket proxy:
   \[
   w_i \sigma_i
   \]
3. optional realized-risk contribution proxy from rolling covariance

Show the top contributors.

### D. Data quality diagnostics

Show:

- missing-vol counts by ticker
- missing-price counts by ticker
- first / last valid date by ticker
- dropped dates after alignment
- warning if too many constituents are missing on the latest date

---

## Required visualizations (Plotly)

Use Plotly for all charts. Keep them interactive, readable, and trading-desk friendly.

### 1) Historical implied correlation chart

Primary chart.

Requirements:

- line chart of daily implied correlation (full formula)
- optional overlay of approximate implied correlation
- optional overlay of rolling realized correlation
- optional shaded bands for percentile zones or rolling min/max
- hover tooltips with date, basket vol, weighted constituent vol, implied corr, realized corr

### 2) Vol comparison chart

Show:

- basket implied vol
- weighted average constituent implied vol
- maybe weighted average constituent variance transformed into vol-equivalent if helpful

### 3) Spread chart

Show:

- implied correlation minus realized correlation
- optional zero reference line

### 4) Contribution chart

Show one or both:

- horizontal bar chart of top constituent contributions to weighted single-name variance
- treemap of constituent weights × vols

### 5) Correlation heatmap (optional but highly desirable)

Using realized returns, show rolling or latest realized correlation matrix for constituents.

This is not the same as implied correlation, but it helps portfolio intuition.

### 6) Scatter plot (desirable)

Scatter of:

- x-axis: constituent weight
- y-axis: constituent implied vol
- marker size: contribution to weighted variance
- label / hover: ticker

---

## UI / UX requirements

Use Streamlit and organize the app into sections:

1. **Sidebar** for inputs and controls
2. **Top summary row** with KPIs
3. **Main analytics tabs**:
   - Overview
   - Historical Correlation
   - Vol Diagnostics
   - Constituents
   - Data Quality
   - Methodology

### Overview tab

Should contain:

- snapshot metrics
- quick interpretation text
- latest top contributors
- small preview of uploaded basket table

### Historical Correlation tab

Should contain:

- primary implied-correlation chart
- spread chart
- exportable time-series table

### Vol Diagnostics tab

Should contain:

- vol comparison chart
- tables for basket vol vs weighted constituent vol
- percentile / z-score diagnostics

### Constituents tab

Should contain:

- contribution bar chart
- scatter plot
- constituent-level raw data table

### Data Quality tab

Should contain:

- missing data diagnostics
- list of excluded tickers and reasons
- date coverage summary

### Methodology tab

Should contain:

- formulas rendered in Markdown / LaTeX
- explanation of assumptions
- warning that constant implied correlation is a simplification
- explanation of difference between implied correlation, realized correlation, and dispersion-trade PnL

---

## Engineering requirements

### 1) Code quality

Use:

- Python 3.11+
- type hints everywhere reasonable
- dataclasses or pydantic models where useful
- small focused modules
- docstrings for public functions
- logging, not print statements
- no notebook-style code inside app logic

### 2) Suggested project structure

```text
project_root/
  app.py
  README.md
  requirements.txt
  .gitignore
  data/
    vols/
    prices/
    samples/
  src/
    config.py
    models.py
    data_provider.py
    loaders.py
    validators.py
    analytics/
      implied_corr.py
      realized_corr.py
      contributions.py
      alignment.py
    charts/
      correlation_charts.py
      vol_charts.py
      contribution_charts.py
    ui/
      sidebar.py
      tables.py
      messages.py
    utils/
      dates.py
      formatting.py
      stats.py
  tests/
    test_validators.py
    test_implied_corr.py
    test_realized_corr.py
    test_alignment.py
```

### 3) Separation of concerns

Keep separate:

- file parsing / validation
- data fetching
- alignment and cleaning
- analytics
- plotting
- UI rendering

### 4) Streamlit best practices

Use Streamlit caching appropriately for deterministic expensive operations, especially data loading and transformations. Uploaded files are handled in-memory by Streamlit and can be persisted across reruns through caching / session-state-aware design, so structure the app accordingly. Prefer `st.file_uploader` for the basket CSV and `st.plotly_chart` for visualization. Plotly line charts should sort data by date before plotting to avoid incorrect pathing.  

### 5) Error handling

Handle gracefully:

- missing ticker files
- partially missing histories
- mismatched date ranges
- empty result after alignment
- zero or near-zero denominator in implied-correlation formula
- negative implied correlation or >100% implied correlation

Do not silently suppress issues. Surface them clearly in the UI.

### 6) Numerical robustness

- ensure weights are normalized to sum to 1 internally
- use decimal vols internally
- clip or flag impossible outputs rather than hide them
- document when output is unstable because denominator is too small
- make the calculation reproducible and deterministic

---

## Detailed calculation requirements

### Historical implied correlation series

For each date in the aligned vol dataset:

1. Get basket vol \(\sigma_I(t)\)
2. Get each constituent vol \(\sigma_i(t)\)
3. Normalize weights to sum to 1
4. Compute:

\[
A_t = \sum_i w_i^2 \sigma_i(t)^2
\]

\[
B_t = \sum_{i \neq j} w_i w_j \sigma_i(t) \sigma_j(t)
\]

\[
\rho_{imp}(t) = \frac{\sigma_I(t)^2 - A_t}{B_t}
\]

5. Save `rho_imp_full`
6. Also compute:

\[
\rho_{imp}^{approx}(t) = \frac{\sigma_I(t)^2}{\sum_i w_i \sigma_i(t)^2}
\]

7. Add quality flags:
   - insufficient constituents
   - denominator too small
   - out-of-bounds result

### Rolling realized correlation series

For each rolling window ending at date \(t\):

1. Get aligned constituent returns matrix
2. Compute covariance matrix \(\Sigma_t\)
3. Compute realized constituent vols from diagonal of covariance matrix
4. Compute basket realized variance:

\[
\sigma_{basket,realized,t}^2 = w^T \Sigma_t w
\]

5. Compute realized average correlation proxy using constant-correlation form
6. Save `rho_realized`

### Optional extensions (nice to include if time permits)

- EWMA realized covariance option
- exponentially weighted implied-correlation percentile
- z-score of implied correlation
- constituent exclusion threshold based on missingness
- compare current implied correlation with trailing mean / min / max

---

## Interpretation layer requirements

Create a small interpretation engine that writes neutral summary text based on the latest metrics.

Examples of acceptable outputs:

- "Current implied correlation is 72%, which is in the 88th percentile of the selected lookback period."
- "Basket implied vol is elevated relative to the weighted constituent vol basket proxy."
- "Implied correlation is above rolling realized correlation by 11 correlation points."
- "The largest weighted-variance contributors are BNP FP Equity, SAN SQ Equity, and DBK GY Equity."

Avoid simplistic language like "therefore buy X" or "this is definitely cheap".

---

## Outputs and deliverables

You must deliver:

1. Full Streamlit app source code
2. Sample mock CSV data for at least:
   - one basket ticker (e.g. `SX7P Index`)
   - several constituents sufficient to demonstrate analytics
3. One sample basket-upload CSV for SX7P constituents
4. `README.md` with setup and usage instructions
5. `requirements.txt`
6. Unit tests for core calculations
7. Clear placeholder / adapter instructions for swapping in the real cloud database later

---

## Testing requirements

Write tests that verify:

### Implied correlation math

- exact formula works for simple manually checkable baskets
- approximation formula is computed separately
- outputs remain stable under weight normalization
- denominator edge cases are handled

### Data validation

- uploaded file schema is validated
- duplicate tickers are rejected
- invalid weight sums are flagged

### Alignment

- date intersection logic behaves correctly
- missing series are reported

### Realized correlation

- rolling covariance calculation produces expected shape and sensible outputs

---

## Acceptance criteria

The project is successful only if all of the following hold:

1. User can upload a basket CSV and the app runs end-to-end with mock data.
2. The app computes and plots a historical **implied correlation** time series.
3. The app computes a historical **rolling realized correlation** comparison series.
4. The app clearly shows the difference between:
   - basket implied vol,
   - weighted constituent vols,
   - implied correlation,
   - realized correlation.
5. Code is modular enough that `MockCsvDataProvider` can later be replaced by the production cache class with minimal app changes.
6. The README is good enough for another developer to run the app without guessing.

---

## Nice-to-have enhancements

If time permits, add:

- downloadable CSV export of calculated analytics
- downloadable PNG / HTML chart export
- rolling realized-correlation matrix heatmap animation or date slider
- support for multiple tenors and deltas
- support for comparing two uploaded baskets side by side
- support for using a user-uploaded historical data pack instead of local CSV files

---

## Implementation notes and preferences

- Keep the design simple, clean, and desk-friendly.
- Prefer readability over visual gimmicks.
- The methodology should be transparent.
- Make the formulas visible in the app.
- Make it obvious which values are assumptions or approximations.
- Start with SX7P-style European bank names as the sample basket, but do not hardcode logic to SX7P only.
- Use Plotly for charts and pandas / numpy for analytics.
- The app should be runnable locally with a standard `streamlit run app.py` command.

---

## Short implementation plan

1. Create project skeleton and mock CSV data.
2. Build data provider abstraction and mock provider.
3. Build upload parser and basket validator.
4. Build aligned vol and price time-series loader.
5. Implement implied-correlation analytics.
6. Implement realized-correlation analytics.
7. Implement contribution analytics.
8. Build Plotly charts.
9. Build Streamlit UI with tabs and metrics.
10. Add tests, README, and sample files.

---

## Final instruction

Do not return a high-level sketch only. Produce the actual working project files.

The result should be a developer-friendly MVP that is analytically correct, visually usable, and easy to migrate from mock CSV data to the real cache-based data source later.

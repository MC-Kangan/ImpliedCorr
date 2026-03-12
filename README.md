# Implied Correlation Streamlit App

This project is a modular Streamlit MVP for analysing implied correlation of an equity index or custom basket using uploaded constituent weights and local mock CSV market data.

## Features

- Upload a basket file where the first row is the basket ticker and the remaining rows are constituents.
- Compute historical implied correlation with the full constant-correlation formula and the shortcut approximation.
- Compare implied correlation with rolling realized correlation from constituent price history.
- Inspect weighted variance contributors, volatility diagnostics, and data quality warnings.
- Keep the data layer abstract so `MockCsvDataProvider` can later be swapped for a production cache adapter.

## Project structure

- `app.py`: Streamlit entry point.
- `src/data_provider.py`: abstract provider plus CSV mock and cloud stub.
- `src/validators.py`: basket upload parsing and validation.
- `src/analytics/`: data alignment, implied correlation, realized correlation, and contributions.
- `src/charts/`: Plotly chart builders.
- `src/ui/`: Streamlit sidebar, tables, and interpretation text.
- `scripts/generate_mock_data.py`: deterministic mock data generator.
- `data/samples/sx7p_members.csv`: sample upload file.
- `tests/`: unit tests for validation, alignment, implied correlation, and realized correlation.

## Theory notes

The full implied-correlation implementation uses:

```math
\rho_{imp}(t)=\frac{\sigma_I(t)^2-\sum_i w_i^2 \sigma_i(t)^2}{\sum_{i \neq j} w_i w_j \sigma_i(t)\sigma_j(t)}
```

with the off-diagonal denominator computed as:

```math
\left(\sum_i w_i \sigma_i(t)\right)^2-\sum_i w_i^2 \sigma_i(t)^2
```

This is algebraically identical to summing all ordered off-diagonal pairs and matches the variance identity in the build prompt. The realized-correlation proxy uses the same decomposition with rolling constituent covariance matrices. The app also shows the shortcut approximation separately and labels it as an approximation.

The methodology tab explains why implied correlation is a simplification and why dispersion-trade PnL is not the same thing as a pure correlation swap payoff.

## Setup

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Generate the deterministic mock data:

```bash
python scripts/generate_mock_data.py
```

4. Run the app:

```bash
streamlit run app.py
```

## Using the app

1. Upload `data/samples/sx7p_members.csv` or a file in the same format.
2. Choose the date range, realized window, return type, and data-cleaning options from the sidebar.
3. Review the KPI row, historical charts, constituent contributions, and methodology tab.

## Swapping in the real data source later

The UI and analytics only depend on the `DataProvider` protocol. To migrate to production:

1. Implement a provider class that adapts the real cache interface to:
   - `get_vol(ticker, delta, tenor, start_date, end_date)`
   - `px(ticker, start_date, end_date)`
2. Instantiate that provider in `app.py` instead of `MockCsvDataProvider`.
3. Keep the returned DataFrame schema the same:
   - Vols: `date,ticker,delta,tenor,implied_vol`
   - Prices: `date,ticker,close`

No analytics modules need to change if the provider preserves that contract.

## Running tests

The tests use Python's built-in `unittest` runner, so you can run them even before adding `pytest`:

```bash
python -m unittest discover -s tests
```


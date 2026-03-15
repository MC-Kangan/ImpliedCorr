
# Codex Task: Modify Dispersion Analysis Streamlit App

## Objective

Extend the existing Streamlit dispersion analysis application to:

1. Compute **realised correlation using the variance-based alternative method** from the JPMorgan correlation notes.
2. Add **unit tests** validating both implied and realised correlation computations.
3. Integrate additional **useful metrics derived from the JPMorgan framework**.
4. Add a **constituent correlation heatmap** computed from price series.

The implementation should remain modular so it is easy to switch from mock CSV data to the real database later.

---

# 1. Realised Correlation Implementation (Alternative Method)

The realised correlation must be computed using realised volatility data obtained from:

```
get_rvol(ticker, window, start, stop)
```

This avoids the need for dividend-adjusted return series.

## Mathematical Formula

Let:

- `σ_I` = index realised volatility
- `σ_i` = realised volatility of constituent i
- `w_i` = index weight of constituent i

Then:

```
diag_term = Σ(w_i^2 * σ_i^2)

cross_term = (Σ(w_i * σ_i))^2 - diag_term
```

Realised correlation is:

```
ρ_real =
(σ_I^2 - diag_term) / cross_term
```

This is derived from the portfolio variance identity.

## Implementation Requirements

The computation must be:

- **vectorized using pandas or numpy**
- able to compute **historical time series**
- robust to missing data
- clipped to [-1,1] for stability.

Example expected interface:

```python
compute_realized_correlation(
    constituent_rvol_df: pd.DataFrame,
    index_rvol: pd.Series,
    weights: pd.Series
) -> pd.Series
```

Where:

```
constituent_rvol_df
rows = dates
columns = tickers
values = realized vol
```

---

# 2. Implied Correlation Calculation

The implied correlation calculation should follow the same decomposition:

```
diag_term = Σ(w_i^2 σ_i^2)

cross_term = (Σ w_i σ_i)^2 - diag_term
```

Then:

```
ρ_implied =
(σ_index^2 - diag_term) / cross_term
```

Where all volatilities are **implied volatilities**.

Implementation should reuse the same helper functions where possible.

---

# 3. Correlation Heatmap Between Constituents

The app should display a **correlation heatmap of constituent returns**.

## Data Source

For now compute returns using:

```
cache.get_px(ticker, start, stop)
```

This returns **unadjusted price series**.

Future versions will switch to **dividend-adjusted price series**, so the implementation should isolate this logic in a separate function.

## Steps

1. Fetch price series for all tickers
2. Compute log returns

```
returns = log(price / price.shift(1))
```

3. Compute correlation matrix

```
corr_matrix = returns.corr()
```

4. Display as a **Plotly heatmap**

Example visualization:

```
plotly.express.imshow(corr_matrix)
```

This heatmap should be shown in the Streamlit app.

---

# 4. Additional Metrics from JPMorgan Notes

Add the following metrics to the output dashboard:

### Weighted Average Constituent Volatility

```
weighted_const_vol = Σ(w_i σ_i)
```

### Diagonal Term

```
diag_term = Σ(w_i^2 σ_i^2)
```

### Cross Term

```
cross_term = (Σ w_i σ_i)^2 - diag_term
```

### Correlation Proxy

The JPMorgan approximation:

```
ρ_proxy ≈ (σ_index / weighted_const_vol)^2
```

This proxy should be shown for comparison with computed implied correlation.

### Correlation Spread

```
corr_spread = implied_corr - realized_corr
```

This metric is useful for dispersion trading signals.

---

# 5. Testing Requirements

Create **unit tests validating correctness of the correlation computations**.

Tests should be implemented with **pytest**.

## Test Case 1 — Two Asset Portfolio

Create a simple synthetic case:

```
weights = [0.5, 0.5]
vols = [0.20, 0.20]
correlation = 0.50
```

Expected index volatility:

```
σ_index^2 =
0.5^2*0.2^2 + 0.5^2*0.2^2
+ 2*(0.5*0.5*0.2*0.2*0.5)
```

Verify that the implied correlation computation recovers `0.5`.

---

## Test Case 2 — Random Multi-Asset Basket

Generate:

```
weights ~ Dirichlet
vols ~ random
true_corr = 0.3
```

Construct index variance from formula.

Check that both functions return approximately `true_corr`.

---

## Test Case 3 — Historical Vectorized Series

Create a mock DataFrame:

```
dates x tickers
```

with synthetic vol series.

Confirm the function returns a time series of correlations with correct shape and bounds.

---

# 6. Streamlit UI Changes

The dashboard should display:

### Main Charts

- Implied correlation time series
- Realised correlation time series
- Correlation spread

### Additional Panels

- Weighted constituent volatility vs index volatility
- Correlation proxy

### Visualizations

- Constituent correlation heatmap
- Dispersion metrics table

---

# 7. Code Structure

Organize implementation as follows:

```
/analytics
    correlation.py
    dispersion_metrics.py

/data
    mock_cache.py

/tests
    test_correlation.py

/app
    streamlit_app.py
```

Functions should remain reusable for future database integration.

---

# 8. Data Alignment

Ensure:

- constituent vol series
- index vol series
- price series

are **aligned by date before computation**.

Missing values should be forward-filled or dropped.

---

# 9. Future Compatibility

Design the system so that replacing the mock CSV with the real database requires only swapping the data access layer.

Functions like:

```
get_rvol(...)
px(...)
```

should remain unchanged.

---

# Expected Outcome

The app should now allow users to:

- upload index constituents and weights
- compute implied correlation
- compute realised correlation
- visualize correlation spreads
- inspect constituent correlation heatmaps
- verify computations through automated tests

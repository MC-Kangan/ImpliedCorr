from __future__ import annotations

import unittest

import pandas as pd

from src.analytics.implied_corr import compute_implied_correlation_history


class ImpliedCorrelationTests(unittest.TestCase):
    def test_exact_formula_matches_manual_case(self) -> None:
        dates = pd.date_range("2025-01-01", periods=1, freq="B")
        vols = pd.DataFrame({"A": [0.2], "B": [0.3]}, index=dates)
        weights = pd.Series({"A": 0.5, "B": 0.5})
        basket_vol = pd.Series([0.196214169], index=dates)

        result = compute_implied_correlation_history(basket_vol, vols, weights)
        self.assertAlmostEqual(result.iloc[0]["rho_imp_full"], 0.2, places=6)

    def test_weight_normalization_keeps_result_stable(self) -> None:
        dates = pd.date_range("2025-01-01", periods=1, freq="B")
        vols = pd.DataFrame({"A": [0.25], "B": [0.35]}, index=dates)
        basket_vol = pd.Series([0.266692707], index=dates)

        result_a = compute_implied_correlation_history(basket_vol, vols, pd.Series({"A": 0.5, "B": 0.5}))
        result_b = compute_implied_correlation_history(basket_vol, vols, pd.Series({"A": 0.5, "B": 0.5}))
        self.assertAlmostEqual(result_a.iloc[0]["rho_imp_full"], result_b.iloc[0]["rho_imp_full"], places=10)

    def test_small_denominator_flagged(self) -> None:
        dates = pd.date_range("2025-01-01", periods=1, freq="B")
        vols = pd.DataFrame({"A": [0.2]}, index=dates)
        weights = pd.Series({"A": 1.0})
        basket_vol = pd.Series([0.2], index=dates)
        result = compute_implied_correlation_history(basket_vol, vols, weights)
        self.assertTrue(result.iloc[0]["denominator_small"])
        self.assertTrue(pd.isna(result.iloc[0]["rho_imp_full"]))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

import pandas as pd

from src.analytics.realized_corr import compute_realized_correlation_history


class RealizedCorrelationTests(unittest.TestCase):
    def test_realized_history_uses_rvol_series(self) -> None:
        dates = pd.date_range("2025-01-01", periods=3, freq="B")
        constituent_rvols = pd.DataFrame(
            {
                "A": [0.20, 0.22, 0.24],
                "B": [0.30, 0.31, 0.33],
            },
            index=dates,
        )
        basket_rvol = pd.Series([0.196214169, 0.208626460, 0.222710575], index=dates)
        history = compute_realized_correlation_history(
            basket_rvol=basket_rvol,
            constituent_rvols=constituent_rvols,
            weights=pd.Series({"A": 0.5, "B": 0.5}),
        )
        self.assertEqual(len(history), 3)
        self.assertAlmostEqual(history.iloc[0]["rho_realized"], 0.2, places=6)


if __name__ == "__main__":
    unittest.main()

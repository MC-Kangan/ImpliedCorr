from __future__ import annotations

import unittest

import pandas as pd

from src.analytics.realized_corr import compute_realized_correlation_history


class RealizedCorrelationTests(unittest.TestCase):
    def test_realized_history_shape(self) -> None:
        dates = pd.date_range("2025-01-01", periods=6, freq="B")
        prices = pd.DataFrame(
            {
                "A": [100, 101, 102, 101, 103, 104],
                "B": [50, 50.5, 51, 50.8, 51.2, 51.7],
            },
            index=dates,
        )
        history, corr = compute_realized_correlation_history(
            constituent_prices=prices,
            weights=pd.Series({"A": 0.5, "B": 0.5}),
            window=3,
            return_type="log",
        )
        self.assertEqual(len(history), 3)
        self.assertEqual(corr.shape, (2, 2))


if __name__ == "__main__":
    unittest.main()


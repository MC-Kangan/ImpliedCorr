from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from src.analytics.alignment import load_market_data
from src.data_provider import MockCsvDataProvider
from src.validators import parse_basket_csv


class AlignmentTests(unittest.TestCase):
    def test_load_market_data_intersects_dates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        provider = MockCsvDataProvider(vol_dir=root / "data" / "vols", price_dir=root / "data" / "prices")
        payload = (root / "data" / "samples" / "sx7p_members.csv").read_bytes()
        basket = parse_basket_csv(payload).basket

        loaded = load_market_data(
            provider=provider,
            basket=basket,
            start_date=date(2025, 1, 2),
            end_date=date(2025, 12, 31),
            drop_missing_dates=True,
        )
        self.assertFalse(loaded.constituent_vols.empty)
        self.assertEqual(list(loaded.constituent_vols.index), list(loaded.constituent_prices.index))


if __name__ == "__main__":
    unittest.main()


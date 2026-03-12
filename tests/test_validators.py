from __future__ import annotations

import unittest

from src.validators import BasketValidationError, parse_basket_csv


class BasketValidatorTests(unittest.TestCase):
    def test_valid_upload(self) -> None:
        payload = b"ticker,weight\nSX7P Index,100\nSAN SQ Equity,60\nBNP FP Equity,40\n"
        result = parse_basket_csv(payload)
        self.assertEqual(result.basket.basket_ticker, "SX7P Index")
        self.assertAlmostEqual(result.basket.weights.sum(), 1.0)

    def test_duplicate_ticker_rejected(self) -> None:
        payload = b"ticker,weight\nSX7P Index,100\nSAN SQ Equity,60\nSAN SQ Equity,40\n"
        with self.assertRaises(BasketValidationError):
            parse_basket_csv(payload)

    def test_weight_sum_rejected(self) -> None:
        payload = b"ticker,weight\nSX7P Index,100\nSAN SQ Equity,55\nBNP FP Equity,35\n"
        with self.assertRaises(BasketValidationError):
            parse_basket_csv(payload)

    def test_normalize_one_to_hundred(self) -> None:
        payload = b"ticker,weight\nSX7P Index,1\nSAN SQ Equity,0.6\nBNP FP Equity,0.4\n"
        result = parse_basket_csv(payload, normalize_weights_if_one=True)
        self.assertTrue(result.basket.normalized)
        self.assertAlmostEqual(result.basket.weights.sum(), 1.0)


if __name__ == "__main__":
    unittest.main()


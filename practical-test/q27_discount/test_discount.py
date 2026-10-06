import unittest
from decimal import Decimal as D

from discount import apply_discount


class DiscountBoundaryTest(unittest.TestCase):
    def test_boundaries_around_threshold(self):
        cases = [
            ("0", "0.00"),
            ("0.01", "0.00"),
            ("99.99", "0.00"),
            ("100.00", "10.00"),
            ("100.01", "10.00"),
            ("1000000.00", "100000.00"),
        ]
        for total, expected in cases:
            with self.subTest(total=total):
                self.assertEqual(apply_discount(total)[0], D(expected))

    def test_rounding_half_up(self):
        discount, to_pay = apply_discount("100.05")
        self.assertEqual((discount, to_pay), (D("10.01"), D("90.04")))

    def test_negative_total_rejected(self):
        with self.assertRaises(ValueError):
            apply_discount("-1")

    def test_total_is_preserved(self):
        for total in ["0", "50", "99.99", "100", "123.45"]:
            with self.subTest(total=total):
                d, pay = apply_discount(total)
                self.assertEqual(d + pay, D(total))
                self.assertGreaterEqual(pay, 0)

    def test_float_input_does_not_leak_binary_error(self):
        self.assertEqual(apply_discount(100.0)[0], D("10.00"))

    def test_custom_threshold(self):
        self.assertEqual(apply_discount("500", threshold=D("500"))[0], D("50.00"))


if __name__ == "__main__":
    unittest.main()

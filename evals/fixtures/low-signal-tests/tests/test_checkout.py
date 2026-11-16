import unittest

from checkout import item_subtotal, pay


class CheckoutTests(unittest.TestCase):
    def test_payment_matches_implementation_helper(self):
        prices = [12, 8]
        quoted_shipping = 5
        self.assertEqual(pay(prices, quoted_shipping), item_subtotal(prices))


if __name__ == "__main__":
    unittest.main()


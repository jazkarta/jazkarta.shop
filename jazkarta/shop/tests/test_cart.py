from decimal import Decimal
import unittest


class TestLineItem(unittest.TestCase):

    def _makeOne(self, **kw):
        from ..cart import LineItem
        return LineItem(None, None, kw)

    def test_subtotal_rounding(self):
        item = self._makeOne(
            price=Decimal('0.03'),
            discount_pct=Decimal('50.0'),
            coupon='FOO',
        )
        self.assertEqual(item.price, Decimal('0.02'))

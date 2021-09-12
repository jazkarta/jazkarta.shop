from builtins import object
from decimal import Decimal
from zope.interface import implementer

from ..interfaces import ITaxHandler

@implementer(ITaxHandler)
class NoTaxHandler(object):
    """a tax handler that returns zero sales tax.
    """

    label = u'No Sales Tax Handler'

    def get_tax_rates(self, cart):
        return {'Sales Tax': Decimal(0)}

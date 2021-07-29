from builtins import object
from decimal import Decimal
from lxml.etree import fromstring
from zope.interface import implementer
import requests

from ..interfaces import TaxRateException
from ..interfaces import ITaxHandler


WA_STATE_TAX_API_URL = 'http://dor.wa.gov/AddressRates.aspx'


@implementer(ITaxHandler)
class WAStateTaxHandler(object):
    """provide dynamically adjusted tax rate information

    Requires a shopping cart to construct. That cart is assumed to have
    "ship_to" and "data" parameters (both mappings).

    The tax rate will be fetched according to the address information
    present in the ship_to address.

    Uses the WA state tax rate service:

        http://dor.wa.gov/Content/FindTaxesAndRates/RetailSalesTax/DestinationBased/ClientInterface.aspx

    """

    label = u'WA State Tax Handler'

    def get_tax_rates(self, cart):
        ship_to = cart.ship_to
        if ship_to.get('state') not in ('WA', 'Washington'):
            return {}

        rate = fetch_rate(
            ship_to.get('street', None),
            ship_to.get('city', None),
            ship_to.get('postal_code', None),
        )

        if not rate:
            return {}

        return {'WA State Sales Tax': rate}


def fetch_rate(street, city, postal_code):
    params = {
        'city': city,
        'zip': postal_code,
        'addr': street,
        'output': 'xml'
    }

    if not (params['city'] and params['zip'] and params['addr']):
        raise TaxRateException('Missing street, city, or postal_code')

    resp = requests.get(WA_STATE_TAX_API_URL, params=params)
    if not resp.ok:
        # report http errors but wrap in our exception to simplify catching
        msg = "HTTP Error: {}: {}".format(resp.status_code, resp.reason)
        raise TaxRateException(msg)

    result = fromstring(resp.content)

    if result.attrib['code'] not in ('0', '1', '2', '3'):
        # result of 4 or 5 means the API call failed for some reason.
        msg = "Tax API call failed: {}".format(
            result.attrib.get('debughint', 'No API Information Available')
        )
        raise TaxRateException(msg)

    rate = result.attrib['rate'] or '0'
    return Decimal(rate)

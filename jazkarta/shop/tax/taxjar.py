from builtins import object
from decimal import Decimal
from lxml.etree import fromstring
from zope.interface import implementer
import json
import requests

from ..interfaces import TaxRateException
from ..interfaces import ITaxHandler
from ..utils import get_setting

TAXJAR_SMARTCALCS_BASE_URL = 'http://api.taxjar.com/v2/rates/'


@implementer(ITaxHandler)
class TaxJarStateTaxHandler(object):
    """provide dynamically adjusted tax rate information

    Requires a shopping cart to construct. That cart is assumed to have
    "ship_to" and "data" parameters (both mappings).

    The tax rate will be fetched according to the address information
    present in the ship_to address.

    Uses the TarJar SmartCalcs service:

        http://www.taxjar.com/smartcalcs/

    Api key required to be setup in the shop settings panel prior to use.

    """

    label = u'TaxJar SmartCalcs State Tax Handler'

    def get_tax_rates(self, cart):
        ship_to = cart.ship_to
        rate = fetch_rate(
            ship_to.get('street', None),
            ship_to.get('city', None),
            ship_to.get('postal_code', None),
        )

        if not rate:
            return {}

        return {'Sales Tax': rate}


def fetch_rate(street, city, postal_code):
    params = {
        'city': city,
        'zip': postal_code,
        'addr': street,
        'output': 'xml'
    }

    if not (params['city'] and params['zip'] and params['addr']):
        raise TaxRateException('Missing street, city, or postal_code')

    taxjar_api_token = get_setting('taxjar_smartcalcs_api_key')
    headers = {"Authorization" : 'Bearer ' + taxjar_api_token}
    url = TAXJAR_SMARTCALCS_BASE_URL + '/' + params['zip']

    resp = requests.get(url, params=params, headers=headers)

    if not resp.ok:
        # report http errors but wrap in our exception to simplify catching
        msg = "HTTP Error: {}: {}".format(resp.status_code, resp.reason)
        raise TaxRateException(msg)

    result = json.loads(resp.content)
    # TODO add error checking here? does taxjar return error codes?

    rate = result['rate']['combined_rate'] or '0'
    return Decimal(rate)

from datetime import date
from decimal import Decimal
from lxml.etree import fromstring
from lxml.etree import LxmlError
import requests
from .interfaces import TaxRateException


WA_STATE_TAX_API_URL = 'http://dor.wa.gov/AddressRates.aspx'
TAX_QUARTERS = {
    1: 'Q1',
    2: 'Q1',
    3: 'Q1',
    4: 'Q2',
    5: 'Q2',
    6: 'Q2',
    7: 'Q3',
    8: 'Q3',
    9: 'Q3',
    10: 'Q4',
    11: 'Q4',
    12: 'Q4',
}


def date_to_tax_period(date):
    quarter = TAX_QUARTERS[date.month]
    return "%s%s" % (quarter, date.year)


def check_tax_period(tax_period):
    """return True if today falls within the given tax period, False otherwise

    A tax period is assumed to be a string of the form Qxyyyy, where x is an
    integer from 1 to 4 indicating the quarter of the year and 'yyyy' is the
    four-digit year. (see the WA state tax rate service documentation noted in
    the documentation for the Tax class)
    """
    today = date.today()
    quarter = TAX_QUARTERS[today.month]
    year = str(today.year)
    p_quarter = tax_period[:2]
    p_year = tax_period[2:]
    return quarter == p_quarter and year == p_year


class Tax(object):
    """provide dynamically adjusted tax rate information

    Requires a shopping cart to construct. That cart is assumed to have
    "ship_to" and "data" parameters (both mappings). The tax rate will be
    extracted from the data, which must have a 'tax_rate' and 'tax_period'
    key. If the tax period is not current, or either of the two keys are
    missing, the rate will be fetched according to the address information
    present in the ship_to address.

    Uses the WA state tax rate service:

        http://dor.wa.gov/Content/FindTaxesAndRates/RetailSalesTax/DestinationBased/ClientInterface.aspx

    """

    def __init__(self, cart):
        self.cart = cart
        self.ship_to = cart.ship_to
        self.data = cart.data

    @property
    def rate(self):
        # allow for special-case rates that need not be validated for period
        skip_validation = False
        if self.ship_to.get('country') in ('CA', 'Canada'):
            # add 5% GST for Canada orders
            self.data['tax_rate'] = Decimal(0.05)
            self.data['tax_period'] = ''
            skip_validation = True
        elif self.ship_to.get('state') not in ('WA', 'Washington'):
            # outside of WA, do not calculate tax
            self.data['tax_rate'] = Decimal(0)
            self.data['tax_period'] = ''
            skip_validation = True

        if not skip_validation and not self._rate_is_valid():
            self._fetch_rate()
        return Decimal(self.data['tax_rate'])

    @rate.setter
    def rate(self, value):
        self.data['tax_rate'] = value

    @property
    def period(self):
        return self.data.get('tax_period', '')

    @period.setter
    def period(self, value):
        self.data['tax_period'] = value

    def _rate_is_valid(self):
        return (self.data.get('tax_rate', None) is not None and
                self._in_period())

    def _in_period(self):
        return check_tax_period(self.period)

    def _fetch_rate(self):
        params = {
            'city': self.ship_to.get('city', None),
            'zip': self.ship_to.get('postal_code', None),
            'addr': self.ship_to.get('street', None),
            'output': 'xml'
        }

        if not params['city'] and params['zip'] and params['addr']:
            # missing parameters, can't make call, raise error
            msg = 'Unable to calculate rate, missing parameters'
            raise TaxRateException(msg)

        resp = requests.get(WA_STATE_TAX_API_URL, params=params)
        if not resp.ok:
            # report http errors but wrap in our exception to simplify catching
            msg = "HTTP Error: {}: {}".format(resp.status_code, resp.reason)
            raise TaxRateException(msg)

        try:
            result = fromstring(resp.content)
        except LxmlError as e:
            raise TaxRateException(str(e))

        if result.attrib['code'] not in ('0', '1', '2', '3'):
            # result of 4 or 5 means the API call failed for some reason.
            msg = "Tax API call failed: {}".format(
                result.attrib.get('debughint', 'No API Information Available')
            )
            raise TaxRateException(msg)

        raw_rate = result.attrib['rate']
        try:
            self.rate = Decimal(raw_rate)
        except (ValueError, TypeError):
            msg = "Could not convert to decimal: {}".format(raw_rate)
            raise TaxRateException(msg)
        self.period = result.find('addressline').attrib.get(
            'period', date_to_tax_period(date.today()))

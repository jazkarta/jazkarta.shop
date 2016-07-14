from decimal import Decimal
from lxml import etree
import re
import requests
from .utils import get_setting

ENDPOINT = 'http://production.shippingapis.com/ShippingAPI.dll'
DOMESTIC_REQUEST = """<RateV4Request USERID="%(userid)s">
  <Revision>2</Revision>
  <Package ID="0">
    <Service>%(service)s</Service>
    <ZipOrigination>%(origin_zip)s</ZipOrigination>
    <ZipDestination>%(destination_zip)s</ZipDestination>
    <Pounds>%(pounds)s</Pounds>
    <Ounces>%(ounces)s</Ounces>
    <Container></Container>
    <Size>REGULAR</Size>
  </Package>
</RateV4Request>
"""
INTL_REQUEST = """<IntlRateV2Request USERID="%(userid)s">
  <Revision>2</Revision>
  <Package ID="0">
    <Pounds>%(pounds)s</Pounds>
    <Ounces>%(ounces)s</Ounces>
    <MailType>Package</MailType>
    <ValueOfContents></ValueOfContents>
    <Country>%(country)s</Country>
    <Container></Container>
    <Size>REGULAR</Size>
    <Width></Width>
    <Length></Length>
    <Height></Height>
    <Girth></Girth>
    <OriginZip>%(origin_zip)s</OriginZip>
  </Package>
</IntlRateV2Request>
"""

WHITESPACE_RE = re.compile(r'\s+')


def call_usps_api(api, request, params):
    params = params.copy()
    params.update({
        'userid': get_setting('usps_userid'),
        'origin_zip': get_setting('ship_from_zip'),
    })
    request = (request % params).replace('\n', '')
    request = WHITESPACE_RE.sub(' ', request)
    res = requests.get(ENDPOINT, params={
        'API': api,
        'XML': request,
        })
    tree = etree.fromstring(res.content)
    error = None
    if tree.tag == 'Error':
        error = tree
    else:
        error = tree.find('.//Error')
    if error is not None:
        raise Exception('USPS Error: %s' % error.find('Description').text)
    return tree


def expand_weight(weight):
    pounds = int(weight)
    ounces = (weight - int(weight)) * 16
    return pounds, ounces


def calculate_domestic_usps_rate(weight, service_type, destination_zip):
    pounds, ounces = expand_weight(weight)
    usps_services = {'USPS Priority Mail' : 'PRIORITY',
                     'USPS Media Mail' : 'MEDIA'}
    params = {
        'destination_zip': destination_zip,
        'pounds': pounds,
        'ounces': ounces,
        'service': usps_services[service_type],
    }
    res = call_usps_api('RateV4', DOMESTIC_REQUEST, params)
    rate = res.find('.//Postage/Rate').text
    return Decimal(rate)


def calculate_international_usps_rate(weight, country):
    pounds, ounces = expand_weight(weight)
    params = {
        'country': country,
        'pounds': pounds,
        'ounces': ounces,
    }
    res = call_usps_api('IntlRateV2', INTL_REQUEST, params)
    # get the rate for Priority Mail International
    rate = res.find('.//Service[@ID="2"]').find('Postage').text
    return Decimal(rate)


def calculate_usps_rate(weight, service_type, country, zip):
    if country == 'United States':
        return calculate_domestic_usps_rate(weight, service_type, zip)
    else:
        return calculate_international_usps_rate(weight, country)

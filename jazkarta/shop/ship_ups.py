from decimal import Decimal
from ups.client import UPSClient
from ups.model import Package, Address
from jazkarta.shop import config
from .utils import get_settings

UPS_COUNTRY_MAP = dict(config.SHIPPING_COUNTRIES)


def calculate_ups_rates(weight, street, city, state, zip, country):
    settings = get_settings()
    credentials = {
        'username': settings.ups_username,
        'password': settings.ups_password,
        'access_license': settings.ups_api_key,
        'shipper_number': settings.ups_account,
    }
    shipper = Address(
        name=settings.ship_from_name,
        address=settings.ship_from_address,
        city=settings.ship_from_city,
        state=settings.ship_from_state,
        zip=settings.ship_from_zip,
        country=settings.ship_from_country,
    )

    client = UPSClient(credentials, weight_unit='LBS', dimension_unit='IN')
    country = UPS_COUNTRY_MAP[country]
    recipient = Address(
        name='Recipient',
        city=city, address=street, state=state, zip=zip, country=country)
    packages = [Package(weight, 0, 0, 0)]
    res = client.rate(
        packages=packages, packaging_type='02',  # Customer-supplied packaging
        shipper=shipper, recipient=recipient)
    rates = {s['service']: Decimal(s['cost']) for s in res['info']}
    return rates

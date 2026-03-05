from datetime import datetime
from datetime import timedelta
from decimal import Decimal
import threading

import requests

from .config import SHIPPING_COUNTRIES
from .utils import get_setting

ENDPOINT = "https://apis.usps.com"
USPS_COUNTRY_MAP = dict(SHIPPING_COUNTRIES)
USPS_TOKEN = {}
token_update_lock = threading.Lock()


def get_usps_access_token():
    """Get USPS OAuth access token.
    Cache it in a global variable until it expires.
    """
    token = USPS_TOKEN
    with token_update_lock:
        if not token or token["expires_at"] < datetime.now():
            response = requests.post(
                f"{ENDPOINT}/oauth2/v3/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": get_setting('usps_consumer_key'),
                    "client_secret": get_setting('usps_consumer_secret'),
                },
            )
            response.raise_for_status()
            token.update(response.json())
            token["expires_at"] = (
                datetime.fromtimestamp(int(token["issued_at"]) / 1000) +
                timedelta(seconds=int(token["expires_in"]) - 60)
            )
    return token["access_token"]


def calculate_usps_rate(weight, service_type, country, zip):
    access_token = get_usps_access_token()
    origin_zip = get_setting('ship_from_zip')
    options = {
        "priceType": "RETAIL",
        "processingCategory": "NONSTANDARD",
        "rateIndicator": "SP",  # single piece (not flat rate box or envelope)
        "destinationEntryFacilityType": "NONE",
        "originZIPCode": origin_zip,
        "weight": weight,
        "length": 1,
        "width": 1,
        "height": 1,
    }
    # We can't calculate rates without a destination zip code. Returning None
    # will skip this shipping method
    if not zip:
        return None
    if country == "United States":
        endpoint = f"{ENDPOINT}/prices/v3/base-rates/search"
        options["destinationZIPCode"] = zip
        if service_type == "USPS Media Mail":
            options["mailClass"] = "MEDIA_MAIL"
        else:
            options["mailClass"] = "PRIORITY_MAIL"
    else:
        endpoint = f"{ENDPOINT}/international-prices/v3/base-rates/search"
        options["destinationCountryCode"] = USPS_COUNTRY_MAP[country]
        options["foreignPostalCode"] = zip
        options["mailClass"] = "PRIORITY_MAIL_INTERNATIONAL"
    response = requests.post(
        endpoint,
        json=options,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        response.raise_for_status()
    except Exception as err:
        try:
            message = response.json()["response"]["errors"][0]["message"]
        except Exception:
            message = str(err)
        raise Exception(f"USPS error: {message}")
    return Decimal(response.json()["totalBasePrice"])

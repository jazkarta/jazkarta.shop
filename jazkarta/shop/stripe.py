# Make sure we don't import this module recursively via `import stripe`
from __future__ import absolute_import

import stripe

from jazkarta.shop import config
from .interfaces import PaymentProcessingException
from .utils import get_setting


def stripe_amount(dollars):
    """Convert a decimal amount to cents for Stripe."""
    return int(dollars * 100)


def call_stripe(method, url, params):
    if config.IN_PRODUCTION:
        api_key_setting = 'stripe_api_key_production'
    else:
        api_key_setting = 'stripe_api_key_dev'
    api_key = get_setting(api_key_setting)
    api = stripe.APIRequestor(api_key)
    try:
        return api.request(method, url, params)[0]
    except stripe.StripeError as e:
        errmsg = e.json_body['error']['message']
        raise PaymentProcessingException(errmsg)
    except Exception as e:
        raise PaymentProcessingException(str(e))


def process_refund(charge_id, refund_amount):
    return call_stripe('post', '/v1/charges/{}/refunds'.format(charge_id), {
        'amount': stripe_amount(refund_amount),
    })


def process_interactive_payment(cart, card_token, contact_info):
    # Calculate total
    amount = stripe_amount(cart.amount)
    assert amount > 0

    metadata = {
        'email': contact_info['email'],
        'phone': contact_info['phone'],
    }
    shipping = cart.stripe_shipping_summary
    if shipping:
        metadata['ship_to'] = shipping

    # Process the charge using Stripe
    return call_stripe('post', '/v1/charges', {
        'amount': int(amount),
        'currency': 'usd',
        'card': card_token,
        'description': cart.summary,
        'metadata': metadata,
    })

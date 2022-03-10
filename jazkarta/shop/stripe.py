# Make sure we don't import this module recursively via `import stripe`
from __future__ import absolute_import

import six
import stripe

from jazkarta.shop import config
from .interfaces import PaymentProcessingException
from .utils import get_setting


def stripe_amount(dollars):
    """Convert a decimal amount to cents for Stripe."""
    return int(dollars * 100)


def call_stripe():
    if config.IN_PRODUCTION:
        api_key_setting = 'stripe_api_key_production'
    else:
        api_key_setting = 'stripe_api_key_dev'
    stripe.api_key = get_setting(api_key_setting)


def process_interactive_payment(cart, card_token, contact_info):
    call_stripe()

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
    try:
        result = stripe.Charge.create(
            amount = int(amount),
            currency = "usd",
            source = card_token,
            description = cart.summary,
            metadata = metadata
        );
    except stripe.error.StripeError as e:
        errmsg = e.json_body['error']['message']
        raise PaymentProcessingException(errmsg)

    except Exception as e:
        raise PaymentProcessingException(six.text_type(e))

    return result

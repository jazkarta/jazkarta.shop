from plone.app.layout.viewlets.common import ViewletBase

from jazkarta.shop import config
from ..utils import get_setting


STRIPE_JS_HTML = """
    <script type="text/javascript" src="https://js.stripe.com/v3/"></script>
    <script type="text/javascript">
        var card;
        var elements;
        var stripe;
        var mounted;
        document.addEventListener("DOMContentLoaded", function(event) {
            stripe = Stripe('%s');
            elements = stripe.elements();
            card = elements.create('card', {hidePostalCode: true,
                                            iconStyle: 'solid'});
            if ($('#card-element').length) {
                card.mount('#card-element');
                mounted = true;
            }
        });
    </script>
"""


class StripeJS(ViewletBase):
    """ Inject the Stripe.js script tag and configuration if relevant"""

    def render(self):
        if config.IN_PRODUCTION:
            key = get_setting('stripe_pub_key_production')
        else:
            key = get_setting('stripe_pub_key_dev')
        return STRIPE_JS_HTML % key

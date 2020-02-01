from nci.content.browser.donation import DonationForm
from zope.browserpage import ViewPageTemplateFile
from zope.interface import implementer
from ...interfaces import IThankYouView


@implementer(IThankYouView)
class CheckoutThankYou(DonationForm):
    """ Renders the Thank You Page """
    index = ViewPageTemplateFile('../templates/checkout_thankyou.pt')

    def handle_submit(self):
        self.old_cart = self.cart.clone()

    def render(self):
        return self.index()

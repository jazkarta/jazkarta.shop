from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.interface import implementer
from . import CheckoutFormBase
from ...interfaces import IThankYouView


@implementer(IThankYouView)
class CheckoutThankYou(CheckoutFormBase):
    """ Renders the Thank You Page """
    index = ViewPageTemplateFile('../templates/checkout_thankyou.pt')

    @lazy_property
    def amount(self):
        if self.old_cart is not None:
            return self.old_cart.amount

        # self.cart.amount likely never called, since at this stage,
        # self.old_cart should exist and self.cart.amount has been cleared
        return self.cart.amount

    def handle_submit(self):
        pass

    def render(self):
        return self.index()

from zope.browserpage import ViewPageTemplateFile
from zope.interface import implementer
from . import CheckoutFormBase
from ..interfaces import IThankYouView


@implementer(IThankYouView)
class CheckoutThankYou(CheckoutFormBase):
    """ Renders the Thank You Page """
    index = ViewPageTemplateFile('../templates/checkout_thankyou.pt')

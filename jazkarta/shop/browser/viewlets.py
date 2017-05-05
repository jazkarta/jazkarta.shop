from plone.app.layout.viewlets.common import ViewletBase
from Products.Five import BrowserView
from zope.cachedescriptors.property import Lazy as lazy_property
from ..cart import Cart
from ..interfaces import IProduct
from ..interfaces import IPurchaseHandler
from ..utils import format_currency


class CartViewMixin(object):

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)


class CartViewlet(CartViewMixin, ViewletBase):
    """Display the shopping cart in the site header
    """


class CartView(CartViewMixin, BrowserView):
    """Used to re-render the shopping cart via AJAX"""

    def __call__(self):
        # Don't theme this response
        self.request.response.setHeader('X-Theme-Disabled', 'True')

        if 'add' in self.request.form:
            self.cart.add_product(self.request.form['add'])

        # Re-render the cart so the display can be updated
        return self.index()


class AddToCartViewlet(ViewletBase):
    """Display add to cart info and button
    """

    @lazy_property
    def purchasable(self):
        return IPurchaseHandler(self.context)

    @property
    def item_price(self):
        price = IPurchaseHandler(self.context).price
        return format_currency(price)

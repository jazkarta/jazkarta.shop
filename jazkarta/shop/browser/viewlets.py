from builtins import object
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five import BrowserView
from zope.cachedescriptors.property import Lazy as lazy_property
import json
from ..cart import Cart
from ..interfaces import IPurchaseHandler
from ..utils import format_currency


class CartViewMixin(object):

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)


class CartViewlet(ViewletBase):
    """Display the shopping cart in the site header
    """

    def render(self):
        if self.request.URL.split('/')[-1] != 'review-cart':
            return '<div class="jaz-shop-cart-wrapper"></div>'
        return ''


class CartView(CartViewMixin, BrowserView):
    """Used to re-render the shopping cart via AJAX"""

    def __call__(self):
        # Don't theme this response
        self.request.response.setHeader('X-Theme-Disabled', 'True')
        # Avoid caching
        self.request.response.setHeader(
            'Cache-Control', 'max-age=0, no-cache, must-revalidate')

        if 'add' in self.request.form:
            uid = self.request.form['add']
            options = json.loads(self.request.form.get('options') or '{}')
            self.cart.add_product(uid, **options)

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

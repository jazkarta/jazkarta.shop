from builtins import object
from decimal import Decimal
from Products.Five import BrowserView
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.interface import implementer

from ..interfaces import IProduct
from ..interfaces import OutOfStock
from ..interfaces import IDontShowJazkartaShopPortlets
from ..cart import Cart
from ..utils import get_navigation_root_url
from ..utils import get_user_fullname
from ..utils import resolve_uid
from .coupons import CouponCodeForm
from .checkout import P5Mixin


class CartViewMixin(object):

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    def get_user_fullname(self, userid):
        return get_user_fullname(userid)

    def validate_cart(self):
        self.error = None


@implementer(IDontShowJazkartaShopPortlets)
class ReviewCartForm(CartViewMixin, BrowserView, P5Mixin):
    """A form to review the cart and enter coupon codes."""

    cart_template = ViewPageTemplateFile('templates/checkout_cart.pt')
    cart_is_editable = True

    def __call__(self):
        self.coupon_form = CouponCodeForm(self.context, self.request)
        self.coupon_form.update()
        if self.coupon_form.errors:
            return

        self.validate_cart()
        if self.error:
            return

        if 'submitted' in self.request.form:
            base_url = get_navigation_root_url()
            args = ''
            if self.request.form.get("_authenticator") is not None:
                args = '?_authenticator=' + self.request.form.get("_authenticator")
            if self.cart.shippable:
                return self.request.response.redirect(base_url + '/shipping' + args)
            else:
                return self.request.response.redirect(base_url + '/checkout' + args)

        return self.index()

    def coupons(self):
        items = []
        for cart_item in self.cart.items:
            if not cart_item.is_discounted:
                continue
            coupon = resolve_uid(cart_item.coupon)
            discount_amount = Decimal(
                cart_item.price) - Decimal(cart_item.orig_price)
            items.append({
                'description': coupon.description,
                'id': coupon.title,
                'discount': format_discount(coupon),
                'amount': discount_amount,
                'can_remove': True,
            })
        return items


class UpdateCartView(CartViewMixin, BrowserView, P5Mixin):
    """Re-renders just the cart after user takes an AJAX action."""
    index = ViewPageTemplateFile('templates/checkout_cart.pt')
    cart_is_editable = True

    def update(self):
        try:
            if 'add' in self.request.form:
                cart_id = self.request.form['add']
                self.cart[cart_id].quantity += 1

            if 'change' in self.request.form:
                cart_id = self.request.form['change']
                self.cart[cart_id].quantity = int(self.request.form['quantity'])

            if 'remove' in self.request.form:
                cart_id = self.request.form['remove']
                self.cart[cart_id].quantity = 0

            if 'del' in self.request.form:
                cart_id = self.request.form['del']
                self.cart[cart_id].quantity -= 1
        except OutOfStock:
            self.cart_warnings = {
                cart_id: 'Not enough items in stock.',
            }

        self.validate_cart()

    def __call__(self):
        self.update()
        return self.index()


def format_discount(coupon):
    if coupon.unit == '$':
        discount = '$%s' % coupon.amount
    else:
        discount = '%s%%' % int(coupon.amount)
    return discount


class RecommendedProductsView(CartViewMixin, BrowserView):

    def products(self):
        products_in_cart = [el.product for el in self.cart.items]
        result = []

        for item in products_in_cart:
            product = IProduct(item, alternate=None)
            if product is None:
                continue
            for recommended in getattr(product, 'recommended_products', ()):
                obj = recommended.to_object
                if obj not in result and obj not in products_in_cart:
                    result.append(self.get_product_data(obj))
        return result

    def get_product_data(self, product):
        try:
            image_url = product.unrestrictedTraverse('@@images', None).scale('image', 'mini').url
        except (AttributeError, KeyError):
            image_url = None
        return {'obj': product, 'image_url': image_url}

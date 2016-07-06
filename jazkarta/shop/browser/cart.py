from decimal import Decimal
from Products.Five import BrowserView
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property

from ..interfaces import OutOfStock
from ..cart import Cart
from ..utils import get_navigation_root_url
from ..utils import get_user_fullname
from ..utils import resolve_uid
from .promos import PromoCodeForm


class CartViewMixin(object):

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    def get_user_fullname(self, userid):
        return get_user_fullname(userid)

    def validate_cart(self):
        self.error = None


class ReviewCartForm(CartViewMixin, BrowserView):
    """A form to review the cart and enter promo codes."""

    cart_template = ViewPageTemplateFile('templates/checkout_cart.pt')
    cart_is_editable = True

    def __call__(self):
        self.promo_form = PromoCodeForm(self.context, self.request)
        self.promo_form.update()

        self.validate_cart()
        if self.error:
            return

        if 'submitted' in self.request.form:
            base_url = get_navigation_root_url(self.context)
            if self.cart.shippable:
                return self.request.response.redirect(base_url + '/shipping')
            else:
                return self.request.response.redirect(base_url + '/checkout')

        return self.index()

    def promos(self):
        items = []
        for cart_item in self.cart.items:
            if not cart_item.is_discounted:
                continue
            promo = resolve_uid(cart_item.promo)
            discount_amount = Decimal(
                cart_item.price) - Decimal(cart_item.orig_price)
            items.append({
                'description': promo.description,
                'id': promo.title,
                'discount': format_discount(promo),
                'amount': discount_amount,
                'can_remove': not promo.member_discount,
            })
        return items


class UpdateCartView(CartViewMixin, BrowserView):
    """Re-renders just the cart after user takes an AJAX action."""
    index = ViewPageTemplateFile('templates/checkout_cart.pt')
    cart_is_editable = True

    def update(self):
        try:
            if 'add' in self.request.form:
                cart_id = uid = self.request.form['add']
                self.cart.add_product(uid)
            if 'change' in self.request.form:
                cart_id = self.request.form['change']
                self.cart[cart_id].quantity = int(self.request.form['quantity'])

            if 'del' in self.request.form:
                cart_id = self.request.form['del']
                self.cart[cart_id].quantity = 0

            if 'remove' in self.request.form:
                cart_id = self.request.form['remove']
                self.cart[cart_id].quantity -= 1
        except OutOfStock:
            self.cart_warnings = {
                cart_id: 'Not enough items in stock.',
            }

        self.validate_cart()

    def __call__(self):
        self.update()
        return self.index()


def format_discount(promo):
    if promo.unit == '$':
        discount = '$%s' % promo.amount
    else:
        discount = '%s%%' % int(promo.amount)
    return discount

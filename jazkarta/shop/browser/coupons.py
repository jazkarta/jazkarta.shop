from datetime import datetime
from jazkarta.shop import storage
from Products.Five import BrowserView
from ..cart import Cart
from ..utils import get_catalog
from ..utils import get_current_userid


class CouponCodeForm(BrowserView):
    label = u'Coupons'

    def update(self):
        self.errors = []

        code = self.request.form.get('coupon')
        # Since coupon codes are not required, the field may now be empty.
        # This is a way to bypass a scenario where no coupon code exists
        # but the user has hit apply coupon code button
        if not code:
            return

        coupon = find_coupon_by_code(code)
        if coupon is None:
            self.errors.append('The promo code you entered is not valid.')
            return

        # find eligible cart items
        cart = Cart.from_request(self.request)
        eligible_items = []
        most_expensive_item = None
        for cart_item in cart.items:
            # make sure product category matches
            if (coupon.categories and
                    cart_item.category not in coupon.categories):
                continue
            # make sure specific product matches
            # if (coupon.excluded_products and
            #         cart_item.uid in coupon.excluded_products):
            #     continue
            if coupon.product and cart_item.uid != coupon.product:
                continue

            eligible_items.append(cart_item)
            if (most_expensive_item is None or
                    cart_item.price > most_expensive_item.price):
                most_expensive_item = cart_item

        if not eligible_items:
            self.errors.append(
                'The promo code you entered is not valid for any '
                'items in your cart.'
            )
            return

        if coupon.scope == 'One item':
            most_expensive_item.apply_coupon(coupon)
        else:  # All Items
            for item in eligible_items:
                item.apply_coupon(coupon)

        cart.save()

        # Clear coupon from request
        del self.request.form['coupon']


def find_coupon_by_code(code):
    """Find coupons based on a code entered by the user.

    Skips coupons that are not active for the current date.

    Returns None if multiple coupons are found.
    """
    userid = get_current_userid()
    code = code.lower()
    coupons = []
    for b in get_catalog().unrestrictedSearchResults(
            portal_type='jazkarta.cart.coupon'):
        coupon = b._unrestrictedGetObject()

        # skip if it's not the right code
        if coupon.code.lower() != code:
            continue

        # skip if it's not currently active
        if coupon.start and coupon.start > datetime.now():
            continue
        if coupon.end and coupon.end < datetime.now():
            continue

        # limit on number of uses per user
        if coupon.per_user_limit and userid is not None:
            code_use = storage.get_shop_data(
                [userid, 'coupons', coupon.UID()], default=0)
            if code_use >= coupon.per_user_limit:
                continue

        coupons.append(coupon)

    if len(coupons) > 1 or len(coupons) == 0:
        return None
    return coupons[0]

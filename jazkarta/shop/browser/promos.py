from datetime import datetime
from z3c.form import button, form, field
from z3c.form.interfaces import ActionExecutionError
from zope.interface import Interface
from zope.interface import Invalid
from zope import schema
from jazkarta.shop import storage
from ..cart import Cart
from ..utils import get_catalog
from ..utils import get_current_userid


class IPromoCode(Interface):

    promo_code = schema.TextLine(
        title=u'Promo Code',
    )


class PromoCodeForm(form.Form):
    label = u'Discounts'
    description = u'Do you have a promo code?'
    ignoreContext = True
    ignoreRequest = True
    fields = field.Fields(IPromoCode)

    @button.buttonAndHandler(u'Apply')
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            return

        promo = find_promo_by_code(data['promo_code'])
        if promo is None:
            raise ActionExecutionError(
                Invalid(u'The promo code you entered is not valid.'))
            return

        # find eligible cart items
        cart = Cart.from_request(self.request)
        eligible_items = []
        most_expensive_item = None
        for cart_item in cart.items:
            # make sure product category matches
            if (cart_item.category not in promo.category and
                    'Any' not in promo.category):
                continue
            # make sure specific product matches
            if (promo.excluded_products and
                    cart_item.uid in promo.excluded_products):
                continue
            if promo.product and cart_item.uid != promo.product:
                continue

            eligible_items.append(cart_item)
            if (most_expensive_item is None or
                    cart_item.price > most_expensive_item.price):
                most_expensive_item = cart_item

        if not eligible_items:
            raise ActionExecutionError(
                Invalid(u'The promo code you entered is not valid for any '
                        u'items in your cart.'))

        if promo.scope == 'Single Item':
            most_expensive_item.apply_promo(promo)
        else:  # All Items
            for item in eligible_items:
                item.apply_promo(promo)

        cart.save()


def find_promo_by_code(code):
    """Find promos based on a code entered by the user.

    Skips promos that are not active for the current date
    or that are limited to a different user.

    Returns None if multiple promos are found.
    """
    userid = get_current_userid()
    code = code.lower()
    promos = []
    for b in get_catalog().unrestrictedSearchResults(
            portal_type='jazkarta.cart.promo'):
        promo = b._unrestrictedGetObject()

        # skip promo if it's not the right code
        if promo.title.lower() != code:
            continue

        # skip promo if it's not currently active
        if promo.start and promo.start > datetime.now():
            continue
        if promo.end and promo.end < datetime.now():
            continue

        # user limit
        if promo.user and promo.user != userid:
            continue

        # limit on number of uses per user
        if promo.limit and userid is not None:
            code_use = storage.get_shop_data(
                [userid, 'promos', promo.UID()], default=0)
            if code_use >= promo.limit:
                continue

        promos.append(promo)

    if len(promos) > 1 or len(promos) == 0:
        return None
    return promos[0]

from __future__ import division
from builtins import object
from past.utils import old_div
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal
from hashlib import sha1
from persistent.mapping import PersistentMapping
from zope.component import queryUtility
from zope.event import notify
from zope.interface import implementer
import copy
import json

from jazkarta.shop import logger
from jazkarta.shop import storage
from .interfaces import ICart
from .interfaces import IPurchaseHandler
from .interfaces import ITaxHandler
from .interfaces import OutOfStock
from .interfaces import ItemRemoved
from .utils import get_current_userid
from .utils import get_setting
from .utils import get_site
from .utils import resolve_uid


class LineItem(object):
    """A line item in the cart."""

    def __init__(self, cart, cart_id, item):
        self.cart = cart
        self.cart_id = cart_id
        self._item = item

    @property
    def href(self):
        if 'href' in self._item:
            return self._item['href']
        else:
            product = self.product
            if product is not None:
                handler = IPurchaseHandler(self.product, None)
                if handler is not None and hasattr(handler, 'get_obj_href'):
                    return handler.get_obj_href(self.uid)
                return product.absolute_url()

    @property
    def product(self):
        return resolve_uid(self.uid)

    @property
    def quantity(self):
        return self._item['quantity']

    @quantity.setter
    def quantity(self, value):
        # check stock level
        min_stock_level = get_setting('min_stock_level') or 5
        product = self.product
        if product is not None:
            stock_level = getattr(product, 'stock_level', None)
            if (stock_level is not None and value and
                    stock_level - value < min_stock_level):
                raise OutOfStock

        self._item['quantity'] = value

        if value == 0:
            del self.cart._items[self.cart_id]
            notify(ItemRemoved(self.cart))

        self.cart.data['ship_charge'] = Decimal(0)
        self.cart.save()

    @property
    def orig_price(self):
        price = self._item.get('orig_price')
        if price is None:
            price = self._item.get('price')
        return Decimal(price or 0)

    @property
    def discounted_price(self):
        if self._item.get('discount_pct'):
            multiplier = old_div((
                100 - Decimal(self._item['discount_pct'])), Decimal(100))
            price = Decimal(self.orig_price) * multiplier
        else:  # absolute discount
            price = Decimal(self.orig_price) - Decimal(
                self._item['discount_amt'])
        if price < 0:
            price = Decimal(0)
        return price

    @property
    def price(self):
        if 'price_override' in self._item:
            price = self._item['price_override']
        elif 'coupon' in self._item:
            price = self.discounted_price
        else:
            price = self.orig_price
        return price.quantize(Decimal('0.01'))

    @property
    def orig_subtotal(self):
        return Decimal(self.orig_price) * self.quantity

    @property
    def subtotal(self):
        return Decimal(self.price * self.quantity)

    def __getattr__(self, name):
        try:
            return self._item[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def is_discounted(self):
        return bool('coupon' in self._item)

    def apply_coupon(self, coupon):
        self._item['coupon'] = coupon.UID()
        self._item['coupon_code'] = coupon.title
        if coupon.unit == '%':
            if 'discount_amt' in self._item:
                del self._item['discount_amt']
            self._item['discount_pct'] = coupon.amount
        else:  # absolute discount
            if 'discount_pct' in self._item:
                del self._item['discount_pct']
            self._item['discount_amt'] = coupon.amount

    def override_price(self, price):
        self._item['orig_price'] = price
        for field in (
                'coupon', 'coupon_code', 'discount_amt', 'discount_pct'):
            if field in self._item:
                del self._item[field]

    @property
    def is_shippable(self):
        return bool(self._item.get('weight'))


@implementer(ICart)
class Cart(object):

    @classmethod
    def from_request(cls, request, user_id=None, browser_id=None):
        """Get the user's shopping cart.

        The cart is an OrderedDict keyed by product UID.

        It's stored in a BTree on the site,
        keyed by user id for logged-in users
        and by the browser id cookie for anonymous users.
        If a user starts logged out and then logs in, the cart is moved.
        """
        if user_id is None:
            user_id = get_current_userid()
        if browser_id is None:
            browser_id = get_site().browser_id_manager.getBrowserId()

        if user_id is not None:  # logged in
            storage_id = user_id
            data = storage.get_shop_data([user_id, 'cart'])
            if data is None:
                # not found; see if there's an anonymous one
                # we can upgrade to be stored by user id
                data = storage.get_shop_data([browser_id, 'cart'])
                if data is not None:
                    for item in data['items']:
                        try:
                            item['user'] = user_id
                        except TypeError:
                            # we had at least one case in
                            # production of a corrupted cart
                            # just create a new one if it happens
                            data = PersistentMapping()
                            break
                    storage.del_shop_data([browser_id])
                else:
                    # create a new cart
                    data = PersistentMapping()
        else:
            storage_id = browser_id
            data = storage.get_shop_data([browser_id, 'cart'])
            if data is None:
                data = PersistentMapping()

        return Cart(storage_id, data, request)

    def __init__(self, storage_id, data, request):
        if 'items' not in data:
            data['items'] = OrderedDict()
        self._items = data['items']
        self.storage_id = storage_id
        self.data = data
        self.request = request

    def clone(self):
        return Cart(
            self.storage_id,
            copy.deepcopy(self.data),
            self.request,
        )

    # We should be able to check bool(cart) to see if it has items.
    def __bool__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def __contains__(self, cart_id):
        if '_' in cart_id:
            return cart_id in self._items
        else:
            return any(i['uid'] == cart_id for i in list(self._items.values()))

    def __getitem__(self, cart_id):
        return LineItem(self, cart_id, self._items[cart_id])

    def __delitem__(self, cart_id):
        del self._items[cart_id]
        notify(ItemRemoved(self))
        self.save()

    @property
    def items(self):
        return [LineItem(self, k, v) for k, v in list(self._items.items())]

    def save(self):
        """Make sure changes to the cart are persisted.

        This is necessary since OrderedDict isn't persistence-aware.
        """
        self.data['items'] = self._items
        if self.storage_id:
            if len(self.data['items']):
                storage.set_shop_data([self.storage_id, 'cart'], self.data)
            else:
                storage.del_shop_data([self.storage_id, 'cart'])

    def clear(self):
        items = self._items
        items.clear()
        self.data.clear()
        self.data['items'] = items
        self.save()

    @property
    def itemcount(self):
        return sum(i['quantity'] for i in list(self._items.values()))

    @property
    def orig_subtotal(self):
        return sum(item.orig_subtotal for item in self.items)

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items)

    @property
    def discount(self):
        discount = Decimal(0)
        for item in self.items:
            if item.is_discounted:
                unit_discount = Decimal(item.price) - Decimal(item.orig_price)
                item_discount = unit_discount * item.quantity
                discount += item_discount
        return discount

    def calculate_taxes(self):
        rates = OrderedDict()
        for name in get_setting('tax_handlers'):
            tax_handler = queryUtility(ITaxHandler, name=name)
            if tax_handler is None:
                logger.warning(
                    'Tax handler enabled but not found: {}'.format(name))
                continue

            rates.update(tax_handler.get_tax_rates(self))

        taxable_subtotal = sum(
            item.subtotal for item in self.items if item.taxable)
        taxable_subtotal += self.shipping

        taxes = []
        for label, rate in list(rates.items()):
            # Calculate tax, rounded to nearest cent
            tax = (taxable_subtotal * rate).quantize(Decimal('0.01'))
            if tax != 0:
                # only append non-zero taxes to cart
                taxes.append({
                    'label': label,
                    'tax': tax,
                })

        self.data['taxes'] = taxes

    @property
    def taxes(self):
        return self.data.get('taxes', [])

    @property
    def tax_subtotal(self):
        return sum(item['tax'] for item in self.taxes)

    @property
    def amount(self):
        """Total amount to charge for this order.

        Includes optional donation, shipping and tax.
        """
        return self.subtotal + self.tax_subtotal + self.shipping

    def add_product(self, product_uid, userid=None, **kw):
        """Add a product to the cart by UID.

        Extra keyword arguments will be added to the cart item.

        If the item is free (price is 0), its after_purchase method
        will be called immediately and it will not be added to the cart.

        Returns a boolean indicating whether there are items in the
        cart that need checkout.
        """

        context = resolve_uid(product_uid)
        if context is None:
            raise ValueError('Product {} not found.'.format(product_uid))
        purchase_handler = IPurchaseHandler(context)

        needs_checkout = False
        if userid is None:
            userid = get_current_userid()

        cart_items = purchase_handler.get_cart_items(**kw)

        for lineitem_info in cart_items:
            lineitem_info['user'] = userid
            cart_id = lineitem_info['uid'] + '_' + (userid or '')
            if kw:
                cart_id += '_' + sha1(
                    json.dumps(kw, sort_keys=True)).hexdigest()

            lineitem = LineItem(self, cart_id, lineitem_info)

            # If item is free, complete "purchase" immediately
            # rather than adding to cart.
            if not lineitem.price:
                purchase_handler.after_purchase(lineitem_info)
                continue
            else:
                needs_checkout = True

            # Update cart
            if cart_id in self._items:
                self[cart_id].quantity += 1
            else:
                self._items[cart_id] = lineitem_info

        # Make sure changes are persisted
        self.save()
        return needs_checkout

    def add_item(self, item):
        """Add an item to the cart.

        If the item is already in the cart, it is replaced.

        This method is useful for adding a line item
        programmatically even if it's not based on a content item
        that can be adapted to IPurchaseHandler.
        """

        userid = get_current_userid()
        uid = item.get('uid')
        cart_id = item.get('cart_id')

        for k in ('price', 'quantity'):
            if k not in item:
                raise ValueError('Missing item field: {}'.format(k))

        if uid is None and cart_id is None:
            raise ValueError('Item must specify uid or cart_id')
        if cart_id is None:
            cart_id = '{}_{}'.format(uid, userid or '')

        item['user'] = userid
        if cart_id in self._items:
            del self[cart_id]
        self._items[cart_id] = item

        self.save()

    def thankyou_message(self):
        # @@@ get from setting
        thankyou_message_path = 'shop/thank-you'

        try:
            page = get_site().unrestrictedTraverse(thankyou_message_path)
            return page.getText()
        except (AttributeError, KeyError):
            return ''

    @property
    def ship_to(self):
        if 'ship_to' not in self.data:
            self.data['ship_to'] = PersistentMapping()
        return self.data['ship_to']

    @property
    def shippable(self):
        return any(item.is_shippable for item in self.items)

    @property
    def shippable_weight(self):
        return sum(
            getattr(item, 'weight', 0) * item.quantity
            for item in self.items if item.is_shippable)

    @property
    def shippable_subtotal(self):
        return sum(item.subtotal for item in self.items if item.is_shippable)

    @property
    def shipping(self):
        return Decimal(self.data.get('ship_charge', 0))

    @property
    def stripe_shipping_summary(self):
        ship_to = self.data.get('ship_to')
        if ship_to:
            res = """%(first_name)s %(last_name)s
%(street)s
%(city)s, %(state)s %(postal_code)s
%(country)s
""" % ship_to
            return res + '[{}]'.format(self.data.get('ship_method'))

    @property
    def summary(self):
        items = [item.name for item in self.items]
        return u', '.join(items)

    def store_order(self, userid):
        data = copy.deepcopy(self.data)
        now = datetime.now()
        path = ['orders', now]
        ident = '_orders_'
        storage.set_shop_data(path, data)
        if userid is not None:
            path = [userid, 'orders', now]
            ident = userid
            storage.set_shop_data(path, data)
        return '|'.join([ident, path[-1].isoformat()])

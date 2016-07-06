from collections import OrderedDict
from cPickle import dumps, loads
from datetime import datetime
from decimal import Decimal
from persistent.mapping import PersistentMapping
import copy

from jazkarta.shop import storage
from .interfaces import IPurchaseHandler
from .interfaces import OutOfStock
from .tax import Tax
from .utils import get_current_userid
from .utils import get_setting
from .utils import get_site
from .utils import resolve_uid
from .utils import resolve_uid_to_url


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
            return resolve_uid_to_url(self.uid)

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

        self.cart.data['ship_charge'] = Decimal(0)
        self.cart.save()

    @property
    def orig_price(self):
        price = self._item.get('orig_price')
        if price is None:
            price = self._item['price']
        return Decimal(price or 0)

    @property
    def discounted_price(self):
        if self._item.get('discount_pct'):
            multiplier = (
                100 - Decimal(self._item['discount_pct'])) / Decimal(100)
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

    @property
    def tax(self):
        tax = Decimal(0)
        if self._item.get('taxable', False):
            # this is a point at which the TaxRateException might be thrown
            tax = (self.subtotal * self.cart.tax_rate).quantize(Decimal('0.01'))
        return tax

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


class Cart(object):

    @classmethod
    def from_request(cls, request):
        """Get the user's shopping cart.

        The cart is an OrderedDict keyed by product UID.

        It's stored in a session for anonymous users
        and in a BTree on the site for logged-in users.
        If a user starts logged out and then logs in, the cart is moved.
        """
        userid = get_current_userid()
        if userid is not None:  # logged in
            cart = storage.get_shop_data([userid, 'cart'])
            if cart is None:
                # not found; see if there's one in the session
                # we can upgrade to persistent storage
                if request.SESSION.has_key('cart'):
                    # avoid cross-db reference
                    cart = loads(dumps(request.SESSION['cart']))
                    for item in cart['items']:
                        item['user'] = userid
                    del request.SESSION['cart']
                else:
                    # create a new cart
                    cart = PersistentMapping()
                storage.set_shop_data([userid, 'cart'], cart)
        else:
            # not logged in; keep cart in session
            session = request.SESSION
            if not session.has_key('cart'):
                session.set('cart', PersistentMapping())
            cart = session['cart']

        return Cart(cart, request)

    def __init__(self, data, request):
        if 'items' not in data:
            data['items'] = OrderedDict()
        self._items = data['items']
        self.data = data
        self.request = request
        self._tax_calculator = Tax(self)

    def clone(self):
        return Cart(
            copy.deepcopy(self.data),
            self.request,
        )

    # We should be able to check bool(cart) to see if it has items.
    def __nonzero__(self):
        return bool(self._items)

    def __len__(self):
        return len(self._items)

    def __contains__(self, cart_id):
        if '_' in cart_id:
            return cart_id in self._items
        else:
            return any(i['uid'] == cart_id for i in self._items.values())

    def __getitem__(self, cart_id):
        return LineItem(self, cart_id, self._items[cart_id])

    @property
    def items(self):
        return [LineItem(self, k, v) for k, v in self._items.items()]

    def save(self):
        """Make sure changes to the cart are persisted.

        This is necessary since OrderedDict isn't persistence-aware.
        """
        self.data['items'] = self._items

    def clear(self):
        items = self._items
        items.clear()
        self.data.clear()
        self.data['items'] = items

    @property
    def itemcount(self):
        return sum(i['quantity'] for i in self._items.values())

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

    @property
    def tax(self):
        if 'tax_override' in self.data:
            return self.data['tax_override']

        # this is a point at which the TaxRateException might be thrown
        items_tax = sum(item.tax for item in self.items)
        shipping_tax = Decimal(0)

        tax_rate = self.tax_rate
        shipping = self.shipping
        if tax_rate and shipping:
            shipping_tax = (shipping * tax_rate).quantize(Decimal('0.01'))

        return items_tax + shipping_tax

    @property
    def tax_rate(self):
        """Returns the tax rate appropriate for the order's ship_to address.

        If the rate is required and cannot be calculated, this method will
        raise jazkarta.shop.interfaces.TaxRateException
        """
        if not self.ship_to:
            return Decimal(0)

        return self._tax_calculator.rate

    @property
    def amount(self):
        """Total amount to charge for this order.

        Includes optional donation, shipping and tax.
        """
        return self.subtotal + self.tax + self.shipping

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

        for lineitem_info in purchase_handler.get_cart_items():
            lineitem_info.update(kw)
            lineitem_info['user'] = userid
            cart_id = lineitem_info['uid'] + '_' + (userid or '')

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

    def store_order(self, userid):
        if userid is not None:
            data = copy.deepcopy(self.data)
            now = datetime.now()
            storage.set_shop_data([userid, 'orders', now], data)

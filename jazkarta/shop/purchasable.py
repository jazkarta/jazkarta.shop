from builtins import object
from decimal import Decimal
from zope.component import adapter
from zope.interface import implementer
from .interfaces import IProduct, IATProduct
from .interfaces import IPurchaseHandler
from .utils import get_setting, resolve_uid


@implementer(IPurchaseHandler)
@adapter(IProduct)
class DefaultPurchaseHandler(object):

    def __init__(self, context):
        self.context = context

    def in_stock(self):
        min_stock_level = get_setting('min_stock_level')
        if (self.context.stock_level is not None and
                self.context.stock_level < min_stock_level):
            return False
        return True

    def get_cart_items(self, **options):
        # uid_data is an optional parameter that can be provided to this method
        return [{
            'uid': self.context.UID(),
            'name': self.context.title,
            'price': Decimal('{:.2f}'.format(self.price)),
            'quantity': 1,
            'category': self.context.product_category,
            'taxable': self.context.taxable,
            'weight': self.context.weight,
        }]

    def after_purchase(self, item):
        # Override this in a more specific adapter
        pass

    def get_obj_href(self, uid):
        obj = resolve_uid(uid)
        if obj is not None:
            return obj.absolute_url()

    @property
    def price(self):
        return self.context.price


@implementer(IPurchaseHandler)
@adapter(IATProduct)
class DefaultArchetypesPurchaseHandler(object):

    def __init__(self, context):
        self.context = context

    def in_stock(self):
        if self.context.getField('min_stock_level') is None:
            return True # if user has not specified, ignore this feature
        min_stock_level = self.context.getField('min_stock_level').get(self.context)
        if (self.context.stock_level is not None and
                self.context.stock_level < min_stock_level):
            return False
        return True

    def get_cart_items(self, **options):
        # uid_data is an optional parameter that can be provided to this method
        return [{
            'uid': self.context.UID(),
            'name': self.context.Title(),
            'price': Decimal('{:.2f}'.format(self.price)),
            'quantity': 1,
            'category': self.context.product_category,
            'taxable': self.context.taxable,
            'weight': self.context.weight,
        }]

    def after_purchase(self, item):
        # Override this in a more specific adapter
        pass

    def get_obj_href(self, uid):
        obj = resolve_uid(uid)
        if obj is not None:
            return obj.absolute_url()

    @property
    def price(self):
        return Decimal(self.context.getField('price').get(self.context))

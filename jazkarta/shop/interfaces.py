from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield import DictRow
from decimal import Decimal
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.currency.field import Currency
from z3c.form.browser.checkbox import CheckBoxWidget
from zope.interface import alsoProvides
from zope.interface import Interface
from zope.interface import provider
from zope import schema
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from jazkarta.shop import config


@provider(IFormFieldProvider)
class IProduct(Interface):
    """Marker for content that can be purchased."""

    product_category = schema.Choice(
        title=u'Product Category',
        required=False,
        vocabulary='jazkarta.shop.product_categories',
    )

    price = Currency(
        title=u'Unit Price',
        default=Decimal("0.00"),
        min=Decimal("0.00"),
    )

    stock_level = schema.Int(
        title=u'Stock Level',
        description=u'Number of items remaining in warehouse. '
                    u'Leave blank for no limit.',
        required=False,
        min=0,
    )

    taxable = schema.Bool(
        title=u'Taxable?',
        description=u'Is this item subject to WA state sales tax?',
        default=True,
    )

    weight = schema.Float(
        title=u'Weight (lbs)',
        description=u'Used to calculate shipping.',
        required=False,
    )


class IPurchaseHandler(Interface):
    """Handles interaction between a product and the cart."""

    def in_stock():
        """Returns True if this product's stock level is above the minimum."""

    def get_cart_items():
        """Returns a list of items to add to the cart for this product."""

    def after_purchase(item):
        """Perform actions after this product is purchased."""


class ISettings(model.Schema):

    stripe_api_key_dev = schema.TextLine(
        title=u'Stripe Secret Key (Development)',
    )

    stripe_pub_key_dev = schema.TextLine(
        title=u'Stripe Publishable Key (Development)',
    )

    stripe_api_key_production = schema.TextLine(
        title=u'Stripe Secret Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'."
    )

    stripe_pub_key_production = schema.TextLine(
        title=u'Stripe Publishable Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'."
    )

    receipt_subject = schema.TextLine(
        title=u'Subject for Receipt Email',
        default=u'Receipt for your purchase',
    )

    receipt_intro = schema.Text(
        title=u'Receipt Email Introduction',
        description=u'Text displayed at the top of the receipt email.',
    )

    product_categories = schema.List(
        title=u'Product Categories',
        value_type=schema.TextLine(),
        required=False,
        default=[],
    )

    min_stock_level = schema.Int(
        title=u'Minimum Stock Level',
        description=u'If merchandise stock is below this level, '
                    u'the item will not be available for online purchase.',
        default=5,
        min=0,
    )

    ship_from_name = schema.TextLine(title=u'Ship From Name')
    ship_from_address = schema.TextLine(title=u'Ship From Address')
    ship_from_city = schema.TextLine(title=u'Ship From City')
    ship_from_state = schema.TextLine(title=u'Ship From State')
    ship_from_zip = schema.TextLine(title=u'Ship From Zip')
    ship_from_country = schema.Choice(
        title=u'Ship From Country',
        default=u'United States',
        vocabulary='jazkarta.shop.countries',
    )

    ups_username = schema.TextLine(title=u'ups.com Username')
    ups_password = schema.Password(title=u'ups.com Password')
    ups_api_key = schema.TextLine(title=u'UPS API Key')
    ups_account = schema.TextLine(title=u'UPS Account Number')

    usps_userid = schema.TextLine(title=u'USPS User Id')


class IDictField(IField):
    """Marker for form fields that should use the dict data manager."""


class IWeightPrice(model.Schema):
    min = schema.Float(
        title=u'Min Weight',
        required=False,
        )
    form.widget('min', size=4)
    max = schema.Float(
        title=u'Max Weight',
        required=False,
        )
    form.widget('max', size=4)
    rate = Currency(
        title=u'Rate',
        required=False,
        )
    form.widget('rate', size=4)
    is_percent = schema.Bool(
        title=u'Percent',
        default=False,
        )


CALCULATION_METHODS = SimpleVocabulary([
    SimpleTerm(value='weight', token='weight', title=u'By weight'),
    SimpleTerm(value='usps', token='usps', title=u'USPS Priority Mail'),
    SimpleTerm(
        value='ups:UPS Next Day', token='ups_nextday', title=u'UPS Next Day'),
    SimpleTerm(value='ups:UPS 2nd Day', token='ups_2day', title=u'UPS 2nd Day'),
    SimpleTerm(
        value='ups:UPS 3 Day Select', token='ups_3day',
        title=u'UPS 3 Day Select'),
    SimpleTerm(
        value='ups:UPS Standard', token='ups_standard', title=u'UPS Standard'),
])


class IShippingMethod(model.Schema):
    name = schema.TextLine(title=u'Name')
    zones = schema.Set(
        title=u'Zones',
        description=u'Where is this shipping method available?',
        value_type=schema.Choice(
            vocabulary=SimpleVocabulary.fromValues(config.SHIPPING_ZONES)),
        )
    form.widget('zones', CheckBoxWidget)
    min_purchase = Currency(
        title=u'Minimum Purchase',
        description=u'If specified, this shipping method will only be '
                    u'available for orders with a subtotal greater than this '
                    u'value.',
        required=False,
        )
    form.widget('min_purchase', size=3)
    calculation = schema.Choice(
        title=u'Calculation Method',
        vocabulary=CALCULATION_METHODS,
        )
    weight_table = schema.List(
        title=u'Shipping Fee by Weight',
        value_type=DictRow(schema=IWeightPrice)
        )
    form.widget('weight_table', DataGridFieldFactory)


# Make sure shipping method fields will be read/written
# using the DictionaryField manager.
for name, field in schema.getFields(IShippingMethod).items():
    alsoProvides(field, IDictField)


class IShippingAddress(model.Schema):

    first_name = schema.TextLine(
        title=u'First Name',
    )
    last_name = schema.TextLine(
        title=u'Last Name',
    )
    street = schema.TextLine(
        title=u'Address',
    )
    city = schema.TextLine(
        title=u'City',
    )
    country = schema.Choice(
        title=u'Country',
        vocabulary='jazkarta.shop.countries',
    )
    state = schema.TextLine(
        title=u'State/Province',
    )
    postal_code = schema.TextLine(
        title=u'ZIP',
        required=False,
    )


class IStripeEnabledView(Interface):
    """Marker for views that should load the Stripe js"""


# Exceptions

class PaymentProcessingException(Exception):
    """Exception indicating a problem with payment processing."""


class OutOfStock(Exception):
    """Exception indicating that a cart item is out of stock."""


class TaxRateException(Exception):
    """Exception indicating failure to calculate tax rate."""

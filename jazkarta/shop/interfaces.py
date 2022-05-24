try:
    # collective.z3cform.datagridfield < 2.0
    from collective.z3cform.datagridfield import DataGridFieldFactory
    from collective.z3cform.datagridfield import DictRow
except ImportError:
    # collective.z3cform.datagridfield >= 2.0
    from collective.z3cform.datagridfield.datagridfield import DataGridFieldFactory
    from collective.z3cform.datagridfield.row import DictRow
from decimal import Decimal
from plone.app.vocabularies.catalog import CatalogSource
from plone.autoform import directives as form
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from z3c.currency.field import Currency
from z3c.form.browser.checkbox import CheckBoxWidget
from z3c.relationfield.schema import RelationList
from zope.component.interfaces import ObjectEvent
from zope.interface import alsoProvides
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import invariant
from zope.interface import provider
from zope import schema
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.schema.interfaces import IField
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from jazkarta.shop import config

try:
    from plone.app.z3cform.widget import SelectWidget
    SELECT_WIDGET_PRESENT = True
except ImportError:
    # Plone4
    SELECT_WIDGET_PRESENT = False


@provider(IFormFieldProvider)
class IProduct(model.Schema):
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
        description=u'Mark the box if this product is subject to sales tax.',
        default=True,
    )

    weight = schema.Float(
        title=u'Weight (lbs)',
        description=u'Used to calculate shipping.',
        required=False,
    )

    recommended_products = RelationList(
        title=u'Recommended products',
        description=u'Recommendations to users who bought this product, shown during checkout.',
        default=[],
        required=False,
        value_type=schema.Choice(
            source=CatalogSource(
                object_provides='jazkarta.shop.interfaces.IProduct'),
        )
    )

    model.fieldset(
        'shop', label=u"Shop",
        fields=(
            'product_category', 'price', 'stock_level', 'taxable', 'weight', 'recommended_products',
        ),
    )


class IATProduct(IProduct):
    """Marker for content that can be purchased - archetypes compatibility."""
    pass


class IPurchaseHandler(Interface):
    """Handles interaction between a product and the cart."""

    def in_stock():
        """Returns True if this product's stock level is above the minimum."""

    def get_cart_items(**options):
        """Returns a list of items to add to the cart for this product."""

    def after_purchase(item):
        """Perform actions after this product is purchased."""

    def get_obj_href(uid):
        """ Provide a hook by which the link to an item can be customized. """


class ICart(Interface):
    """Marker interface for the cart."""


class ITaxHandler(Interface):

    label = Attribute("""Name shown in UI""")

    def get_tax_rates(cart):
        """Return a label -> rate mapping of tax rates in effect for this cart.
        """


class ICoupon(model.Schema):

    code = schema.TextLine(
        title=u'Code',
    )

    categories = schema.Set(
        title=u'Product Category',
        description=u'If specified, this coupon will only apply to '
                    u'products from the specified categories.',
        value_type=schema.Choice(
            vocabulary='jazkarta.shop.product_categories',
        ),
    )

    scope = schema.Choice(
        title=u'Discount applies to',
        values=(
            u'One item',
            u'All items in cart',
        ),
    )

    amount = Currency(
        title=u'Discount Amount',
    )

    unit = schema.Choice(
        title=u'Discount Unit',
        values=(u'$', u'%'),
    )

    per_user_limit = schema.Int(
        title=u'Use Limit Per User',
        description=u'The number of times this coupon may be used '
                    u'by an individual. Enter 0 for unlimited.',
        default=1,
    )

    product = schema.Choice(
        title=u'Specific Product',
        description=u'Optionally specify one product to which this coupon '
                    u'may be applied.',
        source=CatalogSource(
            object_provides='jazkarta.shop.interfaces.IProduct'),
        required=False,
    )

    # excluded_products = schema.Set(
    #     title=u'Excluded Products',
    #     description=u'Products for which this coupon may not be used.',
    #     value_type=schema.Choice(
    #         source=CatalogSource(
    #             object_provides='jazkarta.shop.interfaces.IProduct'),
    #     ),
    #     required=False,
    # )

    start = schema.Datetime(
        title=u'Start Date',
    )

    end = schema.Datetime(
        title=u'End Date',
    )


class ISettings(model.Schema):

    payment_processor = schema.Choice(
        title=u'Payment Processor',
        description=u"Important - Please make sure that the relevant API keys"
                    u" for the selected payment processor are completed below.",
        vocabulary='jazkarta.shop.payment_processors',
    )

    stripe_api_key_dev = schema.TextLine(
        title=u'Stripe Secret Key (Development)',
        required=False,
    )

    stripe_pub_key_dev = schema.TextLine(
        title=u'Stripe Publishable Key (Development)',
        required=False,
    )

    stripe_api_key_production = schema.TextLine(
        title=u'Stripe Secret Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    stripe_pub_key_production = schema.TextLine(
        title=u'Stripe Publishable Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    authorizenet_api_login_id_dev = schema.TextLine(
        title=u'Authorize.Net API Login ID (Sandbox)',
        required=False,
    )

    authorizenet_transaction_key_dev = schema.TextLine(
        title=u'Authorize.Net Transaction Key (Sandbox)',
        required=False,
    )

    authorizenet_signature_key_dev = schema.TextLine(
        title=u'Authorize.Net Signature Key (Sandbox)',
        required=False,
    )

    authorizenet_api_login_id_production = schema.TextLine(
        title=u'Authorize.Net API Login ID (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    authorizenet_transaction_key_production = schema.TextLine(
        title=u'Authorize.Net Transaction Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    authorizenet_signature_key_production = schema.TextLine(
        title=u'Authorize.Net Signature Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    authorizenet_sim_url_dev = schema.TextLine(
        title=u'Authorize.Net SIM URL (Sandbox)',
        required=False,
    )

    authorizenet_sim_url_production = schema.TextLine(
        title=u'Authorize.Net SIM URL (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
    )

    authorizenet_sim_logo_url = schema.TextLine(
        title=u'Authorize.Net SIM Logo URL',
        description=u"Url path to (optional) logo hosted by Authorize.Net.",
        required=False,
    )

    authorizenet_client_key_dev = schema.TextLine(
        title=u'Authorize.Net Client Key (Sandbox)',
        required=False,
    )

    authorizenet_client_key_production = schema.TextLine(
        title=u'Authorize.Net Client Key (Production)',
        description=u"This key will be used when the JAZKARTA_SHOP_ENV "
                    u"environment variable equals 'production'.",
        required=False,
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

    ups_username = schema.TextLine(
        title=u'ups.com Username',
        description=u"Required if UPS shipping option is being used.",
        required=False,
    )
    ups_password = schema.Password(
        title=u'ups.com Password',
        required=False,
        )
    ups_api_key = schema.TextLine(
        title=u'UPS API Key',
        description=u"Required if UPS shipping option is being used.",
        required=False,
    )
    ups_account = schema.TextLine(
        title=u'UPS Account Number',
        description=u"Required if UPS shipping option is being used.",
        required=False,
    )

    usps_userid = schema.TextLine(
        title=u'USPS WebTools API User Id',
        description=u"Required if USPS shipping option is being used.",
        required=False,
    )

    tax_handlers = schema.List(
        title=u'Calculate Tax Using',
        value_type=schema.Choice(
            vocabulary='jazkarta.shop.tax_handlers',
        ),
        default=[],
    )

    taxjar_smartcalcs_api_key = schema.TextLine(
        title=u'TaxJar SmartCalcs API Token',
        required=False,
        )

    after_checkout_callback_url = schema.TextLine(
        title=u'After checkout callback URL',
        description=u"If specified, users will be redirected "
                    u"to this URL with an 'order_id' parameter, instead "
                    u"of being shown the default 'Thank you' page.",
        required=False,
    )

    @invariant
    def validate_payment_processor_keys(data):
        if data.payment_processor == 'Authorize.Net SIM':
            if data.authorizenet_api_login_id_dev is None or \
                data.authorizenet_transaction_key_dev is None or \
                data.authorizenet_api_login_id_production is None or \
                data.authorizenet_transaction_key_production is None or \
                data.authorizenet_sim_url_production is None or \
                data.authorizenet_sim_url_dev is None:
                raise Invalid(u"Authorize.Net SIM API key data is missing.")
        elif data.payment_processor == 'Stripe':
            if data.stripe_api_key_dev is None or \
                data.stripe_pub_key_dev is None or \
                data.stripe_api_key_production is None or \
                data.stripe_pub_key_production is None:
                raise Invalid(u"Stripe API key data is missing.")

class IBrowserLayer(IDefaultBrowserLayer):
    """Browser layer to mark the request when this product is activated."""


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
    SimpleTerm(
        value='usps:USPS Priority Mail', token='usps_prioritymail',
        title=u'USPS Priority Mail'),
    SimpleTerm(
        value='usps:USPS Media Mail', token='usps_mediamail',
        title=u'USPS Media Mail'),
    SimpleTerm(
        value='ups:UPS Next Day', token='ups_nextday', title=u'UPS Next Day'),
    SimpleTerm(value='ups:UPS 2nd Day', token='ups_2day', title=u'UPS 2nd Day'),
    SimpleTerm(
        value='ups:UPS 3 Day Select', token='ups_3day',
        title=u'UPS 3 Day Select'),
    SimpleTerm(
        value='ups:UPS Standard', token='ups_standard', title=u'UPS Standard'),
    SimpleTerm(value='free', token='free', title=u'Free shipping'),
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
    if SELECT_WIDGET_PRESENT:
        form.widget('country', SelectWidget)

    state = schema.TextLine(
        title=u'State/Province',
    )

    postal_code = schema.TextLine(
        title=u'ZIP',
        required=False,
    )


# Make sure PersistentMapping fields will be read/written
# using the DictionaryField manager.
for s in (IShippingMethod, IShippingAddress):
    for name, field in list(schema.getFields(s).items()):
        alsoProvides(field, IDictField)


class IStripeEnabledView(Interface):
    """Marker for views that should load the Stripe js"""


class IThankYouView(Interface):
    """Marker for the thank you page view"""


# Exceptions

class PaymentProcessingException(Exception):
    """A problem with payment processing."""


class OutOfStock(Exception):
    """A cart item is out of stock."""


class TaxRateException(Exception):
    """Failure to calculate tax rate."""


class IDontShowJazkartaShopPortlets(Interface):
    """marker for views that need not display jazkarta.shop related portlets
    """


# Events

class CheckoutComplete(ObjectEvent):
    """Checkout is complete"""


class ItemRemoved(ObjectEvent):
    """Item removed from cart"""

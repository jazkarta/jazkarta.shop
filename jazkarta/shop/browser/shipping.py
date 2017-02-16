from decimal import Decimal
from persistent.mapping import PersistentMapping
from plone.autoform.form import AutoExtensibleForm
from Products.Five import BrowserView
from z3c.form import button
from z3c.form.form import Form
from z3c.form.interfaces import ActionExecutionError
from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.interface import Invalid
from zope.publisher.interfaces.browser import IPublishTraverse
from ZPublisher.BaseRequest import DefaultPublishTraverse
from jazkarta.shop import config
from jazkarta.shop import storage
from .. import logger
from ..cart import Cart
from ..interfaces import CALCULATION_METHODS
from ..interfaces import IShippingAddress
from ..interfaces import IShippingMethod
from ..ship_ups import calculate_ups_rates
from ..ship_usps import calculate_usps_rate
from ..utils import get_current_userid
from ..utils import PLONE_VERSION


def calculate_shipping(cart, method, addr):
    try:
        weight = cart.shippable_weight
        subtotal = cart.shippable_subtotal

        if weight == 0:
            return 0

        if method['calculation'] == 'weight':
            for row in method['weight_table']:
                if row['min'] and weight < row['min']:
                    continue
                if row['max'] and weight > row['max']:
                    continue
                if row['is_percent']:
                    return subtotal * row['rate'] / Decimal(100)
                else:
                    return row['rate']
        elif method['calculation'].startswith('usps'):
            service = method['calculation'].split(':')[-1]
            return calculate_usps_rate(
                weight, service, addr['country'], addr['postal_code'])
        elif method['calculation'].startswith('ups'):
            service = method['calculation'].split(':')[-1]
            request = getRequest()
            if '_ups_rates' in request.other:  # cache result on request
                rates = request.other['_ups_rates']
            else:
                rates = request.other['_ups_rates'] = calculate_ups_rates(
                    weight, addr['street'], addr['city'], addr['state'],
                    addr['postal_code'], addr['country'])
            if service + ' Air Saver' in rates:
                return rates[service + ' Air Saver']
            if service + ' Air' in rates:
                return rates[service + ' Air']
            return rates.get(service)
        raise NotImplementedError(
            'Cannot calculate shipping by {}'.format(method['calculation']))
    except:
        logger.exception('Could not calculate shipping.')
        return


@implementer(IPublishTraverse)
class ShippingMethodControlPanel(BrowserView):

    @lazy_property
    def shipping_methods(self):
        items = storage.get_shop_data(['shipping_methods'], default={}).items()
        methods = []
        if len(items) == 0:
            return []
        # parse the BTree items into a dict
        for x in range(len(items)):            
            item = items[x][1]
            item.update({'key': items[x][0]})
            methods.append(item)
        return methods

    def format_calculation(self, value):
        return CALCULATION_METHODS.by_value[value].title

    def publishTraverse(self, request, name):
        if name.startswith('++'):
            return DefaultPublishTraverse(self, request).publishTraverse(
                request, name)
        return ShippingMethodForm(self.context, request, name)

    def using_plone5(self):
        import pdb; pdb.set_trace()
        if PLONE_VERSION[0] == 5:
            return True
        return False


class ShippingMethodForm(AutoExtensibleForm, Form):
    schema = IShippingMethod

    def __init__(self, context, request, name):
        super(ShippingMethodForm, self).__init__(context, request)
        self._name = name

    @lazy_property
    def label(self):
        if self.ignoreContext:
            return u'Add Shipping Method'
        else:
            return u'Edit Shipping Method'

    @lazy_property
    def shipping_methods(self):
        return storage.get_shop_data(['shipping_methods'], default={})

    def getContent(self):
        if self._name == '+':
            return
        return self.shipping_methods[self._name]

    @lazy_property
    def ignoreContext(self):
        return bool(self.getContent() is None)

    @button.buttonAndHandler(u'Save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        if self._name == '+':
            method = PersistentMapping()
            if self.shipping_methods:
                shipping_method_id = str(
                    max(int(x) for x in self.shipping_methods.keys()) + 1)
            else:
                shipping_method_id = '0'
        else:
            shipping_method_id = self._name
            method = storage.get_shop_data(
                ['shipping_methods', shipping_method_id])

        method.update(data)
        storage.set_shop_data(['shipping_methods', shipping_method_id], method)

    @button.buttonAndHandler(u'Delete', condition=getContent)
    def handleRemove(self, action):
        del self.shipping_methods[self._name]


class ShippingForm(AutoExtensibleForm, Form):
    schema = IShippingAddress
    template = ViewPageTemplateFile('templates/shipping_form.pt')
    shipping_methods_template = ViewPageTemplateFile(
        'templates/shipping_methods_widget.pt')

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @lazy_property
    def all_shipping_methods(self):
        return storage.get_shop_data(['shipping_methods'], default={})

    def available_shipping_methods(self):
        recipient_address, errors = self.extractData()
        if errors:
            return []

        zones = set()
        country = self.widgets['country'].value
        state = self.widgets['state'].value
        if country == 'United States':
            if state == 'AK':
                zones.add('Alaska')
            elif state == 'HI':
                zones.add('Hawaii')
            else:
                zones.add('US')
            if state in config.WEST:
                zones.add('West')
            elif state in config.MIDWEST:
                zones.add('Midwest')
            elif state in config.EAST:
                zones.add('East')
        elif country == 'Canada':
            zones.add('Canada')
        else:
            zones.add('International')

        cart = self.cart
        methods = []
        for id, method in self.all_shipping_methods.items():
            if (method['min_purchase'] and
                    cart.shippable_subtotal < method['min_purchase']):
                continue
            if not zones.intersection(method['zones']):
                continue
            price = calculate_shipping(cart, method, recipient_address)
            if price is None:
                continue
            methods.append({
                'id': id,
                'name': method['name'],
                'price': Decimal(price),
                })
        methods.sort(key=lambda x: x['price'])
        return methods

    def __call__(self):
        if 'update' in self.request.form:
            self.update()
            return self.shipping_methods_template()
        else:
            return super(AutoExtensibleForm, self).__call__()

    def getContent(self):
        ship_to = self.cart.ship_to
        userid = get_current_userid()
        if not ship_to and userid is not None:
            # This is where we could prefill the current user's address
            # ship_to = extract_shipping_address(userid)
            pass
        return ship_to

    @button.buttonAndHandler(u'Update options', name='update')
    def handleUpdate(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        return self.shipping_methods_template()

    @button.buttonAndHandler(u'Proceed to payment', name='proceed')
    def handleProceed(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        cart = Cart.from_request(self.request)
        order = cart.data

        # save shipping address to order
        ship_to = cart.ship_to
        ship_to.update(data)

        # calculate shipping using selected method, and update order
        method_id = self.request.form['shipping_method']
        method = self.all_shipping_methods[method_id]
        charge = calculate_shipping(cart, method, ship_to)
        if charge is None:
            raise ActionExecutionError(
                Invalid(u'Please select a valid shipping method.'))
        order['ship_method'] = method['name']
        order['ship_charge'] = Decimal(charge).quantize(Decimal('0.01'))

        # This is where we could save the shipping address
        # for use in future orders.

        return self.request.response.redirect(
            self.context.absolute_url() + '/checkout')

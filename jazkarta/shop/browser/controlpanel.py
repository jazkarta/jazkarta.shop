import copy
from BTrees.OOBTree import OOBTree
from cgi import escape
from decimal import Decimal
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from zope.interface import implementer
from z3c.form import form
from zope.browserpage import ViewPageTemplateFile
from ..interfaces import ISettings
from ..interfaces import IDontShowJazkartaShopPortlets
from ..utils import resolve_uid
from ..api import get_order_from_id
from .. import storage
from .. import _
from .checkout import P5Mixin


class SettingsControlPanelForm(RegistryEditForm):
    schema = ISettings


SettingsControlPanelView = layout.wrap_form(
    SettingsControlPanelForm, ControlPanelFormWrapper)
SettingsControlPanelView.label = _(u"Jazkarta Shop Settings")


ORDER_KEYS = ('userid', 'date', 'items', 'ship_to', 'taxes', 'ship_charge', 'total')

def _fetch_orders(part, key=()):
    if isinstance(part, OOBTree):
        for k in part.keys():
            if k in ['cart', 'coupon', 'shipping_methods']:
                continue
            key = key + (k,)
            for data in _fetch_orders(part[k], key):
                yield data
    else:
        if 'orders' in key:
            data = copy.deepcopy(part)
            raw_date = key[-1]
            data['date'] = raw_date.strftime('%Y-%m-%d %I:%M %p') if hasattr(raw_date, 'strftime') else raw_date
            items = data.get('items', {}).values()
            data['date_sort'] = raw_date.isoformat() if hasattr(raw_date, 'isoformat') else ''
            if len(key) == 3:
                data['userid'] = key[0]
                data['orderid'] = '{}|{}'.format(key[0], data['date_sort'])
            else:
                data['userid'] = 'Anonymous'
                data['orderid'] = '_orders_|{}'.format(data['date_sort'])
            data['taxes'] = sum(item.get('tax', 0) for item in data.get('taxes', ()))
            data['total'] = (sum((i.get('price', 0.0) * i.get('quantity', 1)) for i in items) +
                             data['taxes'] + data.get('ship_charge', 0))
            item_str = '<ul>'
            for i in items:
                uid = i.get('uid', None)
                if uid:
                    product = resolve_uid(uid)
                    title = i['name']
                    # do an attr check in case the product is no longer present in the system
                    if hasattr(product,'absolute_url'):
                        href = product.absolute_url()
                    else:
                        href = '';
                else:
                    href = title = i.get('href', '')

                item_str += '<li><a href="{}">{}</a> x {} @ ${}</li>'.format(
                    href, title, i.get('quantity', 1), i.get('price', 0.0)
                )
            data['items'] = item_str + '</ul>'
            address = data.get('ship_to', {})
            data['ship_to'] = u'<p>{} {}</p><p>{}</p><p>{}, {} {}</p><p>{}</p>'.format(
                escape(address.get('first_name', '')),
                escape(address.get('last_name', '')),
                escape(address.get('street', '')),
                escape(address.get('city', '')),
                escape(address.get('state', '')),
                escape(address.get('postal_code', '')),
                escape(address.get('country', '')),
            )
            yield data


class OrderControlPanelForm(form.Form):
    id = "JazkartaShopOrders"
    label = _(u"Jazkarta Shop Orders")


@implementer(IDontShowJazkartaShopPortlets)
class OrderControlPanelView(ControlPanelFormWrapper):
    label = _(u"Jazkarta Shop Orders")
    form = OrderControlPanelForm
    orders = ()
    keys = ORDER_KEYS

    def update(self):
        orders = list(_fetch_orders(storage.get_storage()))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        start = int(self.request.get('b_start', 0))
        self.batch = Batch(orders, size=50, start=start)
        super(OrderControlPanelView, self).update()


@implementer(IDontShowJazkartaShopPortlets)
class OrderDetailsControlPanelView(ControlPanelFormWrapper):
    label = _(u"Jazkarta Shop Order Details")
    form = OrderControlPanelForm
    order_template = ViewPageTemplateFile('templates/checkout_order.pt')

    def update(self):
        order_id = self.request.get('order_id')
        self.order = get_order_from_id(order_id)
        self.order_amount = sum([item['price'] for item in self.order['items'].values()])
        if 'ship_charge' in self.order:
            self.order_amount += self.order['ship_charge']
        if 'taxes' in self.order:
            taxes = Decimal(0)
            for entry in self.order['taxes']:
                taxes += entry['tax']
            self.order_amount += taxes
            self.order_taxes = taxes
        super(OrderDetailsControlPanelView, self).update()

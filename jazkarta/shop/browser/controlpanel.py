import copy
from BTrees.OOBTree import OOBTree
from decimal import Decimal
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from Products.Five.browser import BrowserView
from ..interfaces import ISettings
from ..utils import resolve_uid
from .. import storage
from .. import _


class SettingsControlPanelForm(RegistryEditForm):
    schema = ISettings


SettingsControlPanelView = layout.wrap_form(
    SettingsControlPanelForm, ControlPanelFormWrapper)
SettingsControlPanelView.label = _(u"Jazkarta Shop Settings")


ORDER_KEYS = ('userid', 'date', 'items', 'ship_to', 'taxes', 'ship_charge', 'total')

def _fetch_orders(part, key=()):
    if isinstance(part, OOBTree):
        for k in part.keys():
            if k == 'coupon':
                continue
            key = key + (k,)
            for data in _fetch_orders(part[k], key):
                yield data
    else:
        if 'orders' in key:
            data = copy.deepcopy(part)
            if len(key) == 3:
                data['userid'] = key[0]
            raw_date = key[-1]
            data['date'] = raw_date.strftime('%Y-%m-%d %I:%M %p')
            items = data['items'].values()
            data['date_sort'] = raw_date.isoformat() if hasattr(raw_date, 'isoformat') else ''
            data['taxes'] = sum(item.get('tax', 0) for item in data.get('taxes', ()))
            data['total'] = (sum((i.get('price', 0) * i.get('quantity', 1)) for i in items) +
                             data['taxes'] + Decimal(data.get('ship_charges', 0)))
            items = '<ul>'
            for i in items:
                uid = i.get('uid', None)
                if uid:
                    product = resolve_uid(uid)
                    title = product.Title()
                    href = product.absolute_url()
                else:
                    href = title = i.get('href', '')

                items += '<li><a href="{}">{}</a> x {} @ {}</li>'.format(
                    href, title, i.get('quantity'), i.get('price')
                )
            data['items'] = items + '</ul>'
            address = data['ship_to']
            data['ship_to'] = '<p>{} {}</p><p>{}</p><p>{}, {} {} {}</p>'.format(
                address['first_name'], address['last_name'], address['street'],
                address['city'], address['state'], address['postal_code'],
                address['country']
            )
            yield data


class OrderControlPanelView(BrowserView):
    id = "JazkartaShopOrders"
    label = _(u"Jazkarta Shop Orders")
    description = ""
    form_name = _(u"Jazkarta Shop Orders")
    control_panel_view = "jazkarta-shop-orders"
    orders = ()
    keys = ORDER_KEYS

    def __init__(self, context, request):
        self.context = context
        self.request = request
        orders = list(_fetch_orders(storage.get_storage()))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        start = int(request.get('b_start', 0))
        self.batch = Batch(orders, size=50, start=start)

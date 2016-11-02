import copy
from BTrees.OOBTree import OOBTree
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from Products.Five.browser import BrowserView
from ..interfaces import ISettings
from ..cart import LineItem
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
            data['date'] = key[-1]
            line_items = [LineItem(None, k, v) for k, v in data['items'].items()]
            data['total'] = (sum(i.subtotal for i in line_items) +
                             data.get('taxes') + data.get('ship_charges'))
            items = ''
            for i in data.line_items:
                items += '<p><a href="{}">{}</a> x {} @ {}</p>'.format(
                    i.href, i.product.Title(), i.quantity, i.price
                )
            data['items'] = items
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
        orders.sort(key=lambda o: o.get('date'), reverse=True)
        start = int(request.get('b_start', 0))
        self.batch = Batch(orders, size=50, start=start)

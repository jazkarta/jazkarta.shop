import copy
from BTrees.OOBTree import OOBTree
from cgi import escape
from decimal import Decimal
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from z3c.form import form
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
            data['date'] = raw_date.strftime('%Y-%m-%d %I:%M %p') if hasattr(raw_date, 'strftime') else raw_date
            items = data.get('items', {}).values()
            data['date_sort'] = raw_date.isoformat() if hasattr(raw_date, 'isoformat') else ''
            data['taxes'] = sum(item.get('tax', 0) for item in data.get('taxes', ()))
            data['total'] = (sum((i.get('price', 0.0) * i.get('quantity', 1)) for i in items) +
                             data['taxes'] + data.get('ship_charge', 0))
            item_str = '<ul>'
            for i in items:
                uid = i.get('uid', None)
                if uid:
                    product = resolve_uid(uid)
                    title = i['name']
                    href = product.absolute_url()
                else:
                    href = title = i.get('href', '')

                item_str += '<li><a href="{}">{}</a> x {} @ ${}</li>'.format(
                    href, title, i.get('quantity', 1), i.get('price', 0.0)
                )
            data['items'] = item_str + '</ul>'
            address = data.get('ship_to', {})
            data['ship_to'] = '<p>{} {}</p><p>{}</p><p>{}, {} {}</p><p>{}</p>'.format(
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

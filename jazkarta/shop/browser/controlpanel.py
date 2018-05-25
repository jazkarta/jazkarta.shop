import copy
import csv
import datetime
from BTrees.OOBTree import OOBTree
from cStringIO import StringIO
from DateTime import DateTime
from cgi import escape
from decimal import Decimal
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from Products.Five import BrowserView
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

def _fetch_orders(part, key=(), csv=False):
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

                if csv:
                    # special parsing of items for csv export
                    item_str += '<li><a href="{}">{}</a> x {} @ ${}</li>'.format(
                        href, title, i.get('quantity', 1), i.get('price', 0.0)
                    )
                else:
                    item_str += '• {} x {} @ ${} \n'.format(
                         title, i.get('quantity', 1), i.get('price', 0.0)
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
        orders = list(_fetch_orders(storage.get_storage(), False))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        start = int(self.request.get('b_start', 0))
        self.batch = Batch(orders, size=50, start=start)
        super(OrderControlPanelView, self).update()

    def check_date_integrity(self):
        """ returns False if start_date specified is later than the end_date
        """
        start_date = datetime.datetime.strptime(self.startDateString(),
                                                u'%Y-%m-%d')
        end_date = datetime.datetime.strptime(self.endDateString(), u'%Y-%m-%d')
        if start_date > end_date:
            return False
        return True

    def endDateString(self):
        """ return datestring for end date - date picker
        """
        end_date_day = self.request.get('End-Date_day')
        end_date_month = self.request.get('End-Date_month')
        end_date_year = self.request.get('End-Date_year')

        if end_date_day is not None:
            end_date = datetime.date(int(end_date_year),
                                     int(end_date_month),
                                     int(end_date_day))
        else:
            end_date = datetime.datetime.today()

        return end_date.strftime(u'%Y-%m-%d')

    def startDateString(self):
        """ return datestring for start date - date picker
        """
        start_date_day = self.request.get('Start-Date_day')
        start_date_month = self.request.get('Start-Date_month')
        start_date_year = self.request.get('Start-Date_year')

        if start_date_day is not None:
            start_date = datetime.date(int(start_date_year),
                                       int(start_date_month),
                                       int(start_date_day))
        else:
            start_date = datetime.datetime.today() - datetime.timedelta(365)

        return start_date.strftime(u'%Y-%m-%d')


class ExportShopOrders(BrowserView):
    """ Export selected date range of shop orders into a CSV file, do nothing
        if no orders exist.
    """

    def __call__(self):
        csv_content = None
        # get shop order entries
        orders = list(_fetch_orders(storage.get_storage(), True))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        orders_csv = StringIO()

        if orders is not None and len(orders) > 0:
            writer = csv.DictWriter(orders_csv,
                                fieldnames=['userid', 'date', 'items',
                                            'ship_to', 'taxes', 'ship_charge',
                                            'total'],
                                restval='',
                                extrasaction='ignore',
                                dialect='excel',
                                quoting=csv.QUOTE_ALL
                               )

            # Column titles
            ldict={'userid': "User ID",
                   'date': "Date",
                   'items': "Items",
                   'ship_to': "Ship to",
                   'taxes': "Taxes",
                   'ship_charge': "Ship Charge",
                   'total': "Total",
                  }
            writer.writerow(ldict)

            for order in orders:
                ship_charge = ""
                if 'ship_charge' in order:
                    ship_charge = order['ship_charge']
                ship_to = ""
                if 'ship_to' in order:
                    ship_to = order['ship_to']
                    ship_to = ship_to.replace('</p>', ', ').replace('<p>', '')
                    ship_to = ship_to.rstrip(',')

                ldict={'userid': order['userid'],
                       'date': order['date'],
                       'items': order['items'],
                       'ship_to': ship_to,
                       'taxes': order['taxes'],
                       'ship_charge': ship_charge,
                       'total': order['total'],
                      }
                writer.writerow(ldict)

            csv_content = orders_csv.getvalue()
            orders_csv.close()

            now = DateTime()
            nice_filename = '%s_%s' % ('shop-orders_', now.strftime('%Y%m%d'))

            self.request.response.setHeader("Content-Disposition",
                                            "attachment; filename=%s.csv" %
                                             nice_filename)
            self.request.response.setHeader("Content-Type", "text/csv")
            self.request.response.setHeader("Content-Length", len(csv_content))
            self.request.response.setHeader('Last-Modified',
                                            DateTime.rfc822(DateTime()))
            self.request.response.setHeader("Cache-Control", "no-store")
            self.request.response.setHeader("Pragma", "no-cache")
            self.request.response.write(csv_content)

#        self.request.response.redirect(
#                '/'.join(self.context.getPhysicalPath()))

        return csv_content


@implementer(IDontShowJazkartaShopPortlets)
class OrderDetailsControlPanelView(ControlPanelFormWrapper):
    label = _(u"Jazkarta Shop Order Details")
    form = OrderControlPanelForm
    order_template = ViewPageTemplateFile('templates/checkout_order.pt')

    def update(self):
        order_id = self.request.get('order_id')
        self.order = get_order_from_id(order_id)
        self.amount = sum([item['price'] * item['quantity'] for item in self.order['items'].values()])
        if 'ship_charge' in self.order:
            self.amount += self.order['ship_charge']
        if 'taxes' in self.order:
            taxes = Decimal(0)
            for entry in self.order['taxes']:
                taxes += entry['tax']
            self.amount += taxes
            self.order_taxes = taxes
        super(OrderDetailsControlPanelView, self).update()

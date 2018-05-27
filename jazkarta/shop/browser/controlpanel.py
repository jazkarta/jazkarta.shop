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
            for data in _fetch_orders(part[k], key, csv):
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
            if csv:
                item_str = ''
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
                    item_str += '{} x {} @ ${}'.format(
                         title, i.get('quantity', 1), i.get('price', 0.0)
                    )
                    # add new line character to all but last item
                    if i != items[len(items)-1]:
                        item_str += '\n'
                else:
                    item_str += '<li><a href="{}">{}</a> x {} @ ${}</li>'.format(
                        href, title, i.get('quantity', 1), i.get('price', 0.0)
                    )
            data['items'] = item_str + '</ul>'
            if csv:
                data['items'] = item_str
            address = data.get('ship_to', {})
            if csv:
                data['ship_to'] = u'{} {}, {}, {}, {} {}, {}'.format(
                    escape(address.get('first_name', '')),
                    escape(address.get('last_name', '')),
                    escape(address.get('street', '')),
                    escape(address.get('city', '')),
                    escape(address.get('state', '')),
                    escape(address.get('postal_code', '')),
                    escape(address.get('country', '')),
                )
                # check if shipping address has been entered
                if data['ship_to'].replace(',','').replace(' ','') == '':
                    data['ship_to'] = u''
            else:
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

class DateMixin:
    """ Mixin class that provides datepicker methods.
    """

    # defaults
    first_order_date = datetime.datetime.today() - datetime.timedelta(365)
    last_order_date = datetime.datetime.today()

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
            ed = datetime.date(int(end_date_year),
                               int(end_date_month),
                               int(end_date_day))
        else:
            ed = self.to_datetime(self.most_recent_order_date,
                '%Y-%m-%d %I:%M %p')
        return ed.strftime(u'%Y-%m-%d')

    def startDateString(self):
        """ return datestring for start date - date picker
        """
        start_date_day = self.request.get('Start-Date_day')
        start_date_month = self.request.get('Start-Date_month')
        start_date_year = self.request.get('Start-Date_year')
        if start_date_day is not None:
            sd = datetime.date(int(start_date_year),
                               int(start_date_month),
                               int(start_date_day))
        else:
            sd = self.to_datetime(self.first_order_date, 
                '%Y-%m-%d %I:%M %p')
        return sd.strftime(u'%Y-%m-%d')

    def to_datetime(self, date, date_format):
        return datetime.datetime.strptime(date, date_format)


@implementer(IDontShowJazkartaShopPortlets)
class OrderControlPanelView(ControlPanelFormWrapper, DateMixin, P5Mixin):
    label = _(u"Jazkarta Shop Orders")
    form = OrderControlPanelForm
    orders = ()
    keys = ORDER_KEYS
    end_index = 0
    start_index = 0

    def update(self):
        orders = list(_fetch_orders(storage.get_storage(), (), False))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        start = int(self.request.get('b_start', 0))

        if not self.using_plone5(): # only P4 has date selection at the moment
            self.most_recent_order_date = orders[0]['date']
            self.first_order_date = orders[len(orders)-1]['date']

            # default in case date selection integrity check fails
            # this could happen if end date < start date
            self.end_index = 0 
            self.start_index = len(orders)-1

            selected_start = self.to_datetime(self.startDateString(),'%Y-%m-%d')
            selected_end = self.to_datetime(self.endDateString(),'%Y-%m-%d')

            if self.check_date_integrity():
                # generate list of dates in selected date range
                count = selected_start
                date_range = []
                while count <= selected_end:        
                    date_range.append(count)
                    count += datetime.timedelta(days=1)

                # find orders indexes that are in selected range
                indexes = [ orders.index(x) for x in orders if \
                    self.to_datetime(x['date'], \
                    '%Y-%m-%d %I:%M %p').replace(hour=0, minute=0) in date_range]
                if len(indexes) > 0:
                    self.end_index = indexes[0] # newest 
                    self.start_index = indexes[len(indexes)-1] # oldest
                    # trim orders based on selected start and end 
                    orders = orders[self.end_index:self.start_index]
                else:
                    # no orders in selected date range
                    orders = []

        self.batch = Batch(orders, size=50, start=start)
        super(OrderControlPanelView, self).update()


class ExportShopOrders(BrowserView, DateMixin):
    """ Export selected date range of shop orders into a CSV file, do nothing
        if no orders exist.
    """

    def __call__(self):
        csv_content = None
        # get shop order entries
        orders = list(_fetch_orders(storage.get_storage(), (), True))
        orders.sort(key=lambda o: o.get('date_sort', ''), reverse=True)
        orders_csv = StringIO()

        # get indexes of selected orders dates if supplied
        first_order = self.request.get('first_order')
        last_order = self.request.get('last_order')
        if first_order and last_order:
            try:
                if int(last_order) <= len(orders)-1 and int(first_order) >= 0:
                    # trim selection
                    orders = orders[int(first_order):int(last_order)]
            except:
                pass

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

                ldict={'userid': order['userid'],
                       'date': order['date'],
                       'items': order['items'],
                       'ship_to': order['ship_to'],
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

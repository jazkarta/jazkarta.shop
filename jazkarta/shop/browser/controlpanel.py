from future import standard_library
standard_library.install_aliases()
from builtins import object
import copy
import csv
import datetime
from six import StringIO
from DateTime import DateTime
try:
    from cgi import escape
except ImportError:
    from html import escape
from decimal import Decimal
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.batching import Batch
from plone.z3cform import layout
from Products.Five import BrowserView
from Products.ZCatalog.Lazy import Lazy
from zope.component.hooks import getSite
from zope.interface import implementer
from z3c.form import form
from zope.browserpage import ViewPageTemplateFile
from ..interfaces import ISettings
from ..interfaces import IDontShowJazkartaShopPortlets
from ..utils import resolve_uid
from ..api import get_order_from_id
from .. import storage
from .. import _


class SettingsControlPanelForm(RegistryEditForm):
    schema = ISettings


SettingsControlPanelView = layout.wrap_form(
    SettingsControlPanelForm, ControlPanelFormWrapper)
SettingsControlPanelView.label = _(u"Jazkarta Shop Settings")


ORDER_KEYS = ('userid', 'date', 'items', 'ship_to', 'taxes', 'ship_charge', 'total')


class LazyFilteredOrders(Lazy):
    earliest_date = None
    latest_date = None

    def __init__(self, storage, start_date=None, end_date=None, csv=False):
        self.storage = storage
        self.csv = csv
        # Get all sorted order keys within the date range from the storage without
        # retrieving order data.
        orders = storage.get('orders', {})
        # If we requested read-only storage and it was empty we got a dict which doesn't
        # support key filtering
        if isinstance(orders, dict):
            keys = []
        else:
            keys = list(orders.keys(min=start_date, max=end_date))
        keys.sort(reverse=True)
        self._data = keys
        if len(keys):
            self.earliest_date = keys[-1]
            self.latest_date = keys[0]
        # Optimize Lazy length checks
        self._len = self._rlen = len(keys)

    def __getitem__(self, index):
        user = None
        data = self._data
        date = data[index]
        csv = self.csv
        container = self.storage['orders']
        entry = container[date]
        # Replicate item generation logic from `_fetch_orders` method
        data = copy.deepcopy(entry)
        data['date'] = date.strftime('%Y-%m-%d %I:%M %p') if hasattr(date, 'strftime') else date
        data['date_sort'] = date.isoformat() if hasattr(date, 'isoformat') else ''
        data['taxes'] = sum(item.get('tax', Decimal('0.00')) for item in data.get('taxes', ()))
        items = list(data.get('items', {}).values())
        data['total'] = (sum((i.get('price', Decimal('0.00')) * i.get('quantity', 1)) for i in items) +
                         data['taxes'] + data.get('ship_charge', Decimal('0.00')))

        item_str = u'<ul>'
        if csv:
            item_str = u''
        for i in items:
            # The user id is stored on the line items
            if user is None and i.get('user'):
                user = i['user']
            uid = i.get('uid', None)
            if uid:
                product = resolve_uid(uid)
                title = i['name']
                # do an attr check in case the product is no longer present in
                # the system
                if hasattr(product, 'absolute_url'):
                    href = product.absolute_url()
                else:
                    href = ''
            else:
                href = title = i.get('href', '')

            if csv:
                # special parsing of items for csv export
                item_str += u'{} x {} @ ${}'.format(
                        title, i.get('quantity', 1), i.get('price', Decimal('0.00'))
                )
                # add new line character to all but last item
                if i != items[len(items)-1]:
                    item_str += u'\n'
            else:
                item_str += u'<li><a href="{}">{}</a> x {} @ ${}</li>'.format(
                    href, title, i.get('quantity', 1), i.get('price', Decimal('0.00'))
                )
        data['userid'] = user or u'Anonymous'
        data['orderid'] = '{}|{}'.format(user or '_orders_', data['date_sort'])
        if csv:
            data['items'] = item_str
        else:
            data['items'] = item_str + u'</ul>'
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
            # CSV output needs to be encoded
            data['items'] = data['items'].encode('utf-8')
            data['ship_to'] = data['ship_to'].encode('utf-8')
            data['userid'] = data['userid'].encode('utf-8')
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
        return data


class OrderControlPanelForm(form.Form):
    id = "JazkartaShopOrders"
    label = _(u"Jazkarta Shop Orders")


class SiteSetupLinkMixin(object):
    """ Mixin class that provides site setup url for certain views.
    """

    def plone_control_panel(self):
        return getSite().absolute_url() + '/@@overview-controlpanel'


class DateMixin(object):
    """ Mixin class that provides datepicker methods.
    """

    # defaults
    first_order_date = datetime.date.today() - datetime.timedelta(365)
    last_order_date = datetime.date.today()

    def check_date_integrity(self):
        """ returns False if start_date specified is later than the end_date
        """
        start = self.startDate()
        end = self.endDate()
        if start and end and start >= end:
            return False
        return True

    def endDate(self):
        """ return end date - date picker
        """
        # pat-pickadate gives us a string ex: '2022-12-31'
        end_date = self.request.get('End-Date')

        if end_date:
            # End at midnight the following day
            return datetime.datetime(*map(int, end_date.split('-'))) + datetime.timedelta(days=1)

    def startDate(self):
        """ return start date - date picker
        """

        # pat-pickadate gives us a string ex: '2022-12-31'
        start_date = self.request.get('Start-Date')

        if start_date:
            return datetime.datetime(*map(int, start_date.split('-')))

    def to_datetime(self, date, date_format):
        """ convert to datetime format helper method
        """
        return datetime.datetime.strptime(date, date_format)


@implementer(IDontShowJazkartaShopPortlets)
class OrderControlPanelView(ControlPanelFormWrapper, DateMixin, SiteSetupLinkMixin):
    label = _(u"Jazkarta Shop Orders")
    form = OrderControlPanelForm
    orders = ()
    keys = ORDER_KEYS
    end_index = 0
    start_index = 0
    orders_exist = False

    def update(self):
        start = int(self.request.get('b_start', 0))
        selected_start = self.startDate()
        selected_end = self.endDate()
        order_sequence = LazyFilteredOrders(
            storage.get_storage(), selected_start, selected_end, csv=False
        )
        if len(order_sequence) > 0:
            self.orders_exist = True

        self.batch = Batch(order_sequence, size=50, start=start)
        super(OrderControlPanelView, self).update()


class ExportShopOrders(BrowserView, DateMixin):
    """ Export selected date range of shop orders into a CSV file, do nothing
        if no orders exist.
    """

    def __call__(self):
        csv_content = None
        selected_start = self.startDate()
        selected_end = self.endDate()
        # get shop order entries
        order_sequence = LazyFilteredOrders(
            storage.get_storage(), selected_start, selected_end, csv=True
        )
        orders_csv = StringIO()

        if (order_sequence) > 0:
            writer = csv.DictWriter(
                orders_csv,
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

            for order in order_sequence:
                ship_charge = order.get('ship_charge', '')

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

            # filename generation with date range included
            start = selected_start or order_sequence.earliest_date
            end = selected_end or order_sequence.latest_date
            end_str = end.strftime(u'%m%d%Y')
            start_str = start.strftime(u'%m%d%Y')
            if start_str == end_str:
                nice_filename = '%s_%s' % ('shop_orders', start_str)
            else:
                nice_filename = '%s_%s_%s' % ('shop_orders', start_str, end_str)

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
class OrderDetailsControlPanelView(ControlPanelFormWrapper, SiteSetupLinkMixin):
    label = _(u"Jazkarta Shop Order Details")
    form = OrderControlPanelForm
    order_template = ViewPageTemplateFile('templates/checkout_order.pt')

    def update(self):
        order_id = self.request.get('order_id')
        self.order = get_order_from_id(order_id)
        self.amount = sum([item['price'] * item['quantity'] for item in list(self.order['items'].values())])
        if 'ship_charge' in self.order:
            self.amount += self.order['ship_charge']
        if 'taxes' in self.order:
            taxes = Decimal(0)
            for entry in self.order['taxes']:
                taxes += entry['tax']
            self.amount += taxes
            self.order_taxes = taxes
        super(OrderDetailsControlPanelView, self).update()

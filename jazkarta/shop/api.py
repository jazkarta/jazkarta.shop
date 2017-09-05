from dateutil import parser
from jazkarta.shop import storage


def get_order_from_id(id):
    """ An order_id is a string consisting of the userid and the
    order date in iso format, joined by the pipe character. """
    userid, datestr = id.split('|')
    date = parser.parse(datestr)
    if userid == '_orders_':
        data = storage.get_shop_data(['orders', date])
    else:
        data = storage.get_shop_data([userid, 'orders', date])
    return data

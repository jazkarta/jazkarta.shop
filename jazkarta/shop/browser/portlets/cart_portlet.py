import six
from builtins import object
from zope.interface import implementer
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from Products.Five import BrowserView

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from jazkarta.shop.interfaces import IDontShowJazkartaShopPortlets

from ...cart import Cart


class ICartPortlet(IPortletDataProvider):
    pass


@implementer(ICartPortlet)
class Assignment(base.Assignment):

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return u"Jazkarta Shopping Cart"


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class JazkartaCartPortletMixin(object):

    @property
    def size(self):
        cart = Cart.from_request(self.request)
        if len(cart) == 0:
            return 0
        size = 0
        for x in cart.items:
            size += x.quantity
        return size

    @property
    def cart(self):
        return Cart.from_request(self.request)


class Renderer(base.Renderer, JazkartaCartPortletMixin):
    render = ViewPageTemplateFile('../templates/portlet-cart.pt')

    @property
    def available(self):
        """Portlet is always available.
        The only situation we do not need it is when we display the 
        review-cart, shipping and checkout cart views.
        """
        return not IDontShowJazkartaShopPortlets.providedBy(self.view)


class PortletData(BrowserView, JazkartaCartPortletMixin):
    """ Used for rendering portlet-cart snippet and for serving
        ajax queries related to information about the cart, at the moment
        only the number of items in the cart
    """

    def __call__(self):
        # Avoid caching
        self.request.response.setHeader(
            'Cache-Control', 'max-age=0, no-cache, must-revalidate')
        if 'query' in list(self.request.keys()):
            query = self.request['query']
            if query == 'cart_size':
                return six.text_type(self.size)
            elif query == 'cart_items':
                return "item" if self.size == 1 else "items"
            else:
                return "BAD PORTLET QUERY REQUEST"

        return self.index()

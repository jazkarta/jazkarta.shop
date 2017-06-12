from zope.interface import implements
from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from jazkarta.shop.interfaces import IDontShowJazkartaShopPortlets

from zope.cachedescriptors.property import Lazy as lazy_property
from ...cart import Cart

class ICartPortlet(IPortletDataProvider):
    pass


class Assignment(base.Assignment):
    implements(ICartPortlet)

    @property
    def title(self):
        """Title shown in @@manage-portlets.
        """
        return u"Jazkarta Shopping Cart"


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('../templates/portlet-cart.pt')

    @property
    def available(self):
        """Portlet is always available.
        The only situation we do not need it is when we display the 
        review-cart, shipping and checkout cart views.
        """
        return not IDontShowJazkartaShopPortlets.providedBy(self.view)

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @property
    def size(self):
        return len(Cart.from_request(self.request))

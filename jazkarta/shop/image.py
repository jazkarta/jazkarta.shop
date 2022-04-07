"""Support for products with images
"""
from plone.app.contenttypes.behaviors.leadimage import ILeadImage
from zope.component import adapter
from zope.interface import implementer
from .interfaces import IProductImage


@implementer(IProductImage)
@adapter(ILeadImage)
class LeadImageAdapter(object):
    """
    """

    def __init__(self, context):
        self.context = context

    def url(self):
        obj = ILeadImage(self.context)
        if obj.image is not None:
            return obj.absolute_url() + '/@@images/image/mini'

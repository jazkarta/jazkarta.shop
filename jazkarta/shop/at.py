""" Provide schema extender for archetype CT compatibility
"""
from builtins import object
try:
    from archetypes.schemaextender.field import ExtensionField
    from archetypes.schemaextender.interfaces import ISchemaExtender
    from Products.Archetypes import atapi
except ImportError:
    pass

from jazkarta.shop.interfaces import IATProduct
from zope.component import adapter
from zope.interface import implementer


class ExtendedStringField(ExtensionField, atapi.StringField):
    pass
class ExtendedFixedPointField(ExtensionField, atapi.FixedPointField):
    pass
class ExtendedTextField(ExtensionField, atapi.TextField):
    pass
class ExtendedIntegerField(ExtensionField, atapi.IntegerField):
    pass
class ExtendedBooleanField(ExtensionField, atapi.BooleanField):
    pass
class ExtendedFloatField(ExtensionField, atapi.FloatField):
    pass

@adapter(IATProduct)
@implementer(ISchemaExtender)
class ProductSchemaExtender(object):

    _fields = [
        ExtendedStringField(
            schemata='shop',
            name='product_category',
            required=False,
            enforceVocabulary=True,
            vocabulary_factory='jazkarta.shop.product_categories',
            widget=atapi.SelectionWidget(
                label="Product Category",
                description="Select a product category",
                description_msgid='help_product_category',
            )
        ),
        ExtendedFixedPointField(
            schemata='shop',
            name='price',
            default="0.00",
#        min=Decimal("0.00"),
            widget=atapi.DecimalWidget(
                label="Unit Price",
                description="",
                description_msgid='help_price',
            )
        ),
        ExtendedIntegerField(
            schemata='shop',
            name='stock_level',
            required=False,
#            min=0,
            widget=atapi.IntegerWidget(
                label="Stock Level",
                description="Number of items remaining in warehouse. Leave blank for no limit.",
                description_msgid='help_stock_level',
            )
        ),
        ExtendedBooleanField(
            schemata='shop',
            name='taxable',
            widget=atapi.BooleanWidget(
                label="Taxable?",
                description="Mark the box if this product is subject to sales tax.",
                description_msgid='help_taxable',
            ),
            default=True,
        ),
        ExtendedFloatField(
            schemata='shop',
            name='weight',
            required=False,
            widget=atapi.StringWidget(
                label="Weight (lbs)",
                description="Used to calculate shipping.",
                description_msgid='help_weight',
            )
        )
        ]
        
    def __init__(self, context):
        self.context = context
        
    def getFields(self):
        return self._fields

from jazkarta.shop import config
from zope.component import getUtilitiesFor
from zope.interface import directlyProvides
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from .interfaces import ISettings
from .interfaces import ITaxHandler
from .utils import get_setting


country_names = [c[0] for c in config.SHIPPING_COUNTRIES]
country_vocab = SimpleVocabulary.fromValues(country_names)


def get_country_vocab(context):
    return country_vocab
directlyProvides(get_country_vocab, IVocabularyFactory)


def get_tax_handler_vocab(context):
    terms = []
    for name, utility in sorted(
            getUtilitiesFor(ITaxHandler), key=lambda x: x[1].label):
        terms.append(
            SimpleTerm(value=name, token=name, title=utility.label))
    return SimpleVocabulary(terms)
directlyProvides(get_tax_handler_vocab, IVocabularyFactory)


def get_payment_processor_vocab(context):
    return SimpleVocabulary.fromValues(config.PAYMENT_PROCESSORS)
directlyProvides(get_payment_processor_vocab, IVocabularyFactory)


def vocab_from_setting(setting):
    """Sets up a vocabulary based on a setting."""

    def vocab_factory(context):
        terms = []
        values = get_setting(setting)
        if values is None:
            values = ISettings[setting].default
        for value in values:
            terms.append(SimpleTerm(
                value=value,
                token=value.encode('raw_unicode_escape'),
                title=value,
                ))
        return SimpleVocabulary(terms)
    directlyProvides(vocab_factory, IVocabularyFactory)
    return vocab_factory

product_categories = vocab_from_setting('product_categories')

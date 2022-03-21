from Products.CMFPlone.PloneTool import EMAIL_RE
from zope.interface import Invalid
import re

# make sure hostname has at least two parts
FULL_DOMAIN_RE = re.compile(r'^[^@]+@[^@.]+\.[^@]+$')


def is_email(value):
    # EMAIL_RE may or may not be compiled depending on Plone version,
    # so to be more generally compatible, we use re.match() for this:
    if not re.match(EMAIL_RE, value) or not FULL_DOMAIN_RE.match(value):
        raise Invalid(u'Please enter a valid e-mail address.')
    return True

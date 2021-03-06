from Products.validation.validators.BaseValidators import EMAIL_RE
from zope.interface import Invalid
import re

# make sure hostname has at least two parts
FULL_DOMAIN_RE = re.compile(r'^[^@]+@[^@.]+\.[^@]+$')


def is_email(value):
    if not re.match('^' + EMAIL_RE, value) or not FULL_DOMAIN_RE.match(value):
        raise Invalid(u'Please enter a valid e-mail address.')
    return True

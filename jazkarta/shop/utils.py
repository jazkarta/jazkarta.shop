import six
from AccessControl import getSecurityManager
from Acquisition import aq_inner
from Acquisition import aq_parent
try:
    from email.Header import Header
except ImportError:
    from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from plone import api
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from zope.component.hooks import getSite
from ZODB.POSException import ConflictError
from jazkarta.shop import config
from .interfaces import ISettings
import email
import transaction

PLONE_VERSION = api.env.plone_version()

try:
    from Products.CMFPlone.interfaces.controlpanel import IMailSchema
    REGISTRY_HAS_MAIL_SETTINGS = True
except ImportError:
    # Plone4
    REGISTRY_HAS_MAIL_SETTINGS = False


def get_site():
    """Get the portal.

    It may not be the same as the active component site,
    but should be one of its parents.
    """
    possible_site = aq_inner(getSite())
    while not ISiteRoot.providedBy(possible_site):
        possible_site = aq_parent(possible_site)
    return possible_site


def get_navigation_root_url():
    return getSite().absolute_url()


def get_catalog():
    return getToolByName(get_site(), 'portal_catalog')


def get_current_userid():
    """User ID of current user (or None if logged out)"""
    return getSecurityManager().getUser().getId()


def has_permission(permission, context=None):
    if context is None:
        context = get_site()
    return getSecurityManager().checkPermission(permission, context)


def get_settings():
    registry = getUtility(IRegistry)
    return registry.forInterface(ISettings, False)


def get_setting(name):
    return getattr(get_settings(), name)


def get_user_fullname(userid):
    mtool = getToolByName(get_site(), 'portal_membership')
    member = mtool.getMemberById(userid)
    return member.getProperty('fullname')


def resolve_uid(uid):
    """Less restricted version of plone.app.uuid.utils.uuidToObject

    Given a UID, attempt to return a content object.
    Will return None if the UID can't be found.
    """
    site = get_site()
    if site is None:
        return
    catalog = getToolByName(site, 'portal_catalog', None)
    if catalog is None:
        return
    result = catalog.unrestrictedSearchResults(UID=uid)
    if len(result) != 1:
        return
    return result[0]._unrestrictedGetObject()


def resolve_uid_to_url(uid):
    obj = resolve_uid(uid)
    if obj is not None:
        return obj.absolute_url()


def format_currency(amount):
    return '${:,.2f}'.format(amount)


def send_mail(subject, message, mfrom=None, mto=None):
    site = get_site()
    if message.startswith('<html'):
        portal_transforms = getToolByName(site, 'portal_transforms')
        text = six.text_type(portal_transforms.convert(
            'html_to_web_intelligent_plain_text', message))
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        msg.attach(MIMEText(message, 'html', 'utf-8'))
    else:
        msg = email.message_from_string(message)
        msg.set_charset('utf-8')

    realname = None
    if mfrom is not None:
        realname, replyaddr = email.utils.parseaddr(mfrom)
        msg['Reply-To'] = Header(mfrom, 'utf-8')

    if REGISTRY_HAS_MAIL_SETTINGS:
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(IMailSchema, prefix="plone")
        if not realname:
            realname = mail_settings.email_from_name
        mfrom = email.utils.formataddr((realname, mail_settings.email_from_address))
    else:
        portal = get_site()
        if not realname:
            realname = portal.getProperty('email_from_name')
        mfrom = email.utils.formataddr((realname, portal.getProperty('email_from_address')))

    # Send to portal email address if no recipient was specified,
    # or if we're on a test site
    mailhost = site.MailHost
    if mto is None or not config.IN_PRODUCTION:
        mailhost.send(
            msg, subject=subject, mfrom=mfrom, mto=mfrom,
            immediate=False, charset='utf-8')
    else:
        # send a copy to customer
        mailhost.send(
            msg, subject=subject, mfrom=mfrom, mto=mto,
            immediate=False, charset='utf-8')
        # send a copy to the site owner
        mailhost.send(
            msg, subject=subject, mfrom=mfrom, mto=mfrom,
                immediate=False, charset='utf-8')


def run_in_transaction(retries=5, retry_callback=None):
    """Decorator to run a function in a transaction.

    If a ConflictError occurs when committing, it will retry up to the specified number of times.
    """
    def wrapper(func):
        def run_with_retries(*args, **kw):
            i = retries
            while i > 0:
                try:
                    transaction.begin()
                    res = func(*args, **kw)
                    transaction.commit()
                except ConflictError:
                    transaction.abort()
                    i -= 1
                    if i == 0:
                        raise
                    if retry_callback is not None:
                        retry_callback(*args, **kw)
                else:
                    return res
        return run_with_retries
    return wrapper

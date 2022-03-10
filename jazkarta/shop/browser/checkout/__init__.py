from builtins import range
from builtins import object
from six.moves import range
from datetime import date
from plone.protect.utils import safeWrite
from premailer import Premailer
from Products.Five import BrowserView
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.event import notify
from zope.component import getMultiAdapter
from zope.interface import implementer
from ...cart import Cart
from ...interfaces import CheckoutComplete
from ...interfaces import IDontShowJazkartaShopPortlets
from ...interfaces import TaxRateException
from ...utils import get_setting
from ...utils import has_permission
from ...utils import run_in_transaction
from ...utils import send_mail
from ...utils import PLONE_VERSION
from ...config import EMAIL_CSS
from ...vocabs import country_names
import logging


class P5Mixin(object):
    """ utility method to distinguish between Plone 4 and 5 """

    def using_plone5(self):
        if PLONE_VERSION[0] == '5':
            return True
        return False


@implementer(IDontShowJazkartaShopPortlets)
class CheckoutForm(BrowserView):

    def __call__(self, old_cart=None):
        from .authorize_net_accept_js import CheckoutFormAuthorizeNetAcceptJs
        from .authorize_net_sim import CheckoutFormAuthorizeNetSIM
        from .stripe import CheckoutFormStripe

        payment_processor = get_setting('payment_processor')
        if payment_processor == 'Authorize.Net SIM':
            return CheckoutFormAuthorizeNetSIM(self.context, self.request)()
        elif payment_processor == 'Authorize.Net Accept.js':
            return CheckoutFormAuthorizeNetAcceptJs(
                self.context, self.request)(old_cart)
        elif payment_processor == 'Stripe':
            return CheckoutFormStripe(self.context, self.request)()
        else:
            raise Exception(
                    'No valid payment processor has been specified.')


class CheckoutFormBase(BrowserView, P5Mixin):
    cart_template = ViewPageTemplateFile('../templates/checkout_cart.pt')
    receipt_email = ViewPageTemplateFile('../templates/receipt_email.pt')
    order_template = ViewPageTemplateFile('../templates/checkout_order.pt')

    order_id = None

    def __call__(self, old_cart=None):
        self.old_cart = old_cart
        self.update()
        if 'submitted' in self.request.form:
            self.handle_submit()

        return self.render()

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @lazy_property
    def amount(self):
        return self.cart.amount

    def is_superuser(self):
        return has_permission('Manage portal')

    def update(self):
        self.error = None
        self.mail_not_sent = None

        # only calculate taxes if some items in cart are taxable
        taxable_subtotal = sum(
            item.subtotal for item in self.cart.items if item.taxable)
        if taxable_subtotal != 0:
            try:
                self.cart.calculate_taxes()
            except TaxRateException as e:
                # The sales tax could not be calculated as some of the
                # required information was missing. (can be triggered by anon
                # users, hitting the checkout url directly)
                self.error = ('There was an problem calculating '
                              'the tax: ') + e.args[0]
            if self.error:
                return
            # Make sure writing tax to cart doesn't trigger CSRF warning
            safeWrite(self.cart.data)

        self.prepopulate_billing_info()

    def prepopulate_billing_info(self):
        # Do we want to store contact info?
        # If so we can prefill the form by putting values
        # in the request here.
        pass

    def render(self):
        if 'submitted' in self.request.form and not self.error:
            return self.thankyou_page()
        else:
            return self.index()

    def notify_purchased(self):
        """Notify the CheckedOut event

        This runs after the order has been stored in its own transaction,
        and is the best place to do actions that should only happen once
        and don't have potential for a ConflictError,
        like communication to a non-transactional external service.

        Note: Exceptions here will only abort the final transaction,
        not payment processing or recording of the order.
        """
        notify(CheckoutComplete(self.old_cart))

    @run_in_transaction(retries=5)
    def clear_cart(self):
        """Clear the cart following checkout.

        This is done in a separate transaction so that a cart in the session
        is still intact in case `store_order` needs to be retried.
        """
        self.cart.clear()

    def thankyou_page(self):
        if self.order_id is None:
            # weird edge case I (witekdev) encountered when authorize.net
            # deemed the transaction as a Suspicious Transaction.
            # The browser displayed the following:
            # The reporting of this transaction to the Merchant has timed
            # out. An e-mail has been sent to the merchant informing them
            # of the error. The following is the result of the attempt to
            # charge your credit card.
            # Your order has been received. Thank you for your business!

            # I wasn't able to reproduce this but adding a check if this
            # edge case ever appears again, we can look into it.
            self.error = ('There was an error with your transaction. '
                          'Your payment has not been processed. '
                          'Please contact us for assistance. '
                          '(Internal error: order_id is None)')
            return getMultiAdapter((self.context, self.request),
                                   name="jazkarta.shop.checkout.thank-you")(self.old_cart)

        url = get_setting('after_checkout_callback_url')
        if url:
            order_id = self.order_id
            url = url + "?order_id=%s" % order_id
            if self.mail_not_sent:
                mail_not_sent = self.mail_not_sent
                mail_not_sent.replace(" ", "_")  # encode error message
                url = url + "&mail_not_sent=%s" % mail_not_sent
            if self.error:
                error = self.error
                error.replace(" ", "_")  # encode error message
                url = url + "&error=%s" % error
            self.request.response.redirect(url)
        else:
            return getMultiAdapter((self.context, self.request),
                                   name="jazkarta.shop.checkout.thank-you")(self.old_cart)

    def receipt_intro(self):
        return get_setting('receipt_intro')

    def send_receipt_email(self):
        # Queue receipt email (email is actually sent at transaction commit)
        if self.receipt_email:
            subject = get_setting('receipt_subject')
            unstyled_msg = self.receipt_email()
            msg = Premailer(
                unstyled_msg,
                css_text=EMAIL_CSS,
                cssutils_logging_level=logging.CRITICAL,
            ).transform()
            mto = self.request['email']
            send_mail(subject, msg, mto=mto)
            # assume here that email was sent since stripe does email address
            # validation in the checkout form but this var is needed by
            # the thankyouform due to auth.net requiring it
            self.mail_not_sent = False

    @lazy_property
    def countries(self):
        return country_names

    @lazy_property
    def years(self):
        year = date.today().year
        return list(range(year, year + 11))

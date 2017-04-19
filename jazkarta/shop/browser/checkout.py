import hmac
import time
import random
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
from datetime import date
from hashlib import md5
from persistent.mapping import PersistentMapping
from plone.protect.utils import safeWrite
from premailer import Premailer
from Products.Five import BrowserView
from ZODB.POSException import ConflictError
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.interface import implementer
from zExceptions import Forbidden
from jazkarta.shop import config
from jazkarta.shop import storage
from ..cart import Cart
from ..interfaces import IPurchaseHandler
from ..interfaces import IStripeEnabledView
from ..interfaces import PaymentProcessingException
from ..interfaces import TaxRateException
from ..stripe import process_interactive_payment
from ..utils import get_current_userid
from ..utils import get_setting
from ..utils import has_permission
from ..utils import resolve_uid
from ..utils import run_in_transaction
from ..utils import send_mail
from ..validators import is_email
from ..vocabs import country_names


class CheckoutForm(BrowserView):

    def __call__(self):
        payment_processor = get_setting('payment_processors')
        if payment_processor != []:
            p_p = payment_processor[0]
            if p_p == 'Authorize.Net SIM':
                return CheckoutFormAuthorizeNetSIM(self.context, self.request)()
            elif p_p == 'Stripe':
                return CheckoutFormStripe(self.context, self.request)()
        else:
            raise Exception(
                    'No payment processor has been specified.')


class CheckoutFormAuthorizeNetSIM(BrowserView):
    """ Renders a checkout form with button to submit to Authorize.Net SIM """

    cart_template = ViewPageTemplateFile('templates/checkout_cart.pt')
    thankyou_template = ViewPageTemplateFile('templates/checkout_thankyou.pt')
    index = ViewPageTemplateFile('templates/checkout_form_authorize_net_sim.pt')
    receipt_email = ViewPageTemplateFile('templates/receipt_email.pt')
    post_url_test = 'https://test.authorize.net/gateway/transact.dll'    
    post_url_production = 'https://secure.authorize.net/gateway/transact.dll'

    # Note: Customer only has 15min to complete the checkout process as per:
    # https://support.authorize.net/authkb/index?page=content&id=A592&actp=LIST

    def __call__(self):
        if 'x_response_code' in self.request.form:
            # recreate the cart from session or from storage (by user_id)
            user_id = self.request.form.get('user_id', None)
            session_id = self.request.form.get('session_id', None)
            self.cart = Cart.from_session_id(self.request, user_id, session_id)
        self.update()
        if 'x_response_code' in self.request.form:
            self.handle_submit()
        return self.render()

    def update(self):
        self.error = None
        try:
            self.cart.calculate_taxes()
        except TaxRateException:
            # The sales tax could not be calculated as some of the
            # required information was missing. (can be triggered by anon users,
            # hitting the checkout url directly)
            return 
        # Make sure writing tax to cart doesn't trigger CSRF warning
        safeWrite(self.cart.data)

    def render(self):
        if 'x_response_code' in self.request.form:
            return self.thankyou_template()
        else:
            return self.index()

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @lazy_property
    def amount(self):
        return self.cart.amount
    
    @lazy_property
    def post_url(self):
        if config.IN_PRODUCTION:
            return post_url_production
        else:
            return self.post_url_test

    @lazy_property
    def x_login(self):
        if config.IN_PRODUCTION:
            return get_setting('authorizenet_api_login_id_production')
        else:
            return get_setting('authorizenet_api_login_id_dev')

    @lazy_property
    def transaction_key(self):
        if config.IN_PRODUCTION:
            return get_setting('authorizenet_transaction_key_production')
        else:
            return get_setting('authorizenet_transaction_key_dev')

    @lazy_property
    def x_fp_hash(self):
        """
        x_fp_hash Required.
        Value: The unique transaction fingerprint.
        Notes: The fingerprint is generated using the HMAC-MD5 hashing algorithm 
        on the following field values:
        API login ID (x_login)
        The sequence number of the transaction (x_fp_sequence)
        The timestamp of the sequence number creation (x_fp_timestamp)
        Amount (x_amount)
        Currency code, if submitted (x_currency_code)
        Field values are concatenated and separated by a caret (^).

        Also as per:
        https://support.authorize.net/authkb/index?page=content&id=A569
        trailing ^ is required!!
        APIl0gin1D^Sequence123^1457632735^19.99^
        """
        values = (str(self.x_login), self.x_fp_sequence,
             self.x_fp_timestamp, str(self.amount))
        source = "^".join(values) + '^'
        hashed_values = hmac.new(str(self.transaction_key), '', md5)
        hashed_values.update(source) # add content
        return hashed_values.hexdigest()

    @lazy_property
    def x_fp_sequence(self):
        """
        x_fp_sequence Required
        Value: The merchant-assigned sequence number for the transaction.
        Format: Numeric.
        Notes: The sequence number can be a merchant-assigned value, such as an 
        invoice number or any randomly generated number.
        """
        return str(int(random.random() * 100000000000))

    @lazy_property
    def x_fp_timestamp(self):
        """
        x_fp_timestamp Required
        Value: The timestamp at the time of fingerprint generation.
        Format: UTC time in seconds since January 1, 1970.
        Notes: Coordinated Universal Time (UTC) is an international atomic 
        standard of time
        (sometimes referred to as GMT). Using a local time zone timestamp causes 
        fingerprint authentication to fail.

        In case of error code 97
        For debugging local time vs authorize.net server time
        http://developer.authorize.net/api/reference/responseCode97.html
        """
        return str(int(time.time()))

    @lazy_property
    def session_id(self):
        return self.context.session_data_manager.getBrowserIdManager().getBrowserId()

    @lazy_property
    def user_id(self):
        userid = get_current_userid()
        if userid is not None:
            return userid
        return None

    @lazy_property
    def x_relay_url(self):
        return self.context.absolute_url() + '/checkout'

        # to debug use http://developer.authorize.net/bin/developer/paramdump
        # and to prevent this error:
        # (14) The referrer, relay response or receipt link URL is invalid.
        # return "http://developer.authorize.net/bin/developer/paramdump"
        # also useful:
        # https://support.authorize.net/authkb/index?page=content&id=A663&pmv=print&impressions=false

    @lazy_property
    def x_cancel_url(self):
        # for optional cancel button on SIM form. Take the user to the homepage
        return self.context.absolute_url()

    def handle_submit(self):
        amount = self.amount
        response = self.request['x_response_code']
        if response != '1':
            # Authorize.Net SIM response codes
            # 1 = Approved
            # 2 = Declined
            # 3 = Error
            # 4 = Held for Review
            if 'x_response_reason_text' in self.request.form:
                self.error = self.request['x_response_reason_text']
            else:
                # this scenario unlikely as every response should provide us 
                # with x_response_reason_text
                self.error = ('There was an error with your transaction. '
                              'Your payment has not been processed. '
                              'Please contact us for assistance.')
        if self.error:
            return

        userid = get_current_userid()
        contact_info = PersistentMapping()
        if 'x_first_name' in self.request.form:
            contact_info['first_name'] = self.request.form['x_first_name']
        if 'x_last_name' in self.request.form:
            contact_info['last_name'] = self.request.form['x_last_name']
        if 'x_email' in self.request.form:
            contact_info['email'] = self.request.form['x_email']
        if 'x_phone' in self.request.form:
            contact_info['phone'] = self.request.form['x_phone']
        if 'x_address' in self.request.form:
            contact_info['address'] = self.request.form['x_address']
        if 'x_city' in self.request.form:
            contact_info['city'] = self.request.form['x_city']
        if 'x_state' in self.request.form:
            contact_info['state'] = self.request.form['x_state']
        if 'x_zip' in self.request.form:
            contact_info['zip'] = self.request.form['x_zip']
        if 'x_country' in self.request.form:
            contact_info['country'] = self.request.form['x_country']

        method = 'Online Payment'
        charge_result = {'success': True}

        if not self.error:
            try:
                self.store_order(method, charge_result, userid, contact_info)
                self.clear_cart()
            except ConflictError:
                raise Exception(
                    'Failed to store results of payment after multiple '
                    'retries. Please contact us for assistance.')

    # This code runs after the payment is processed
    # to update various data in the ZODB.
    @run_in_transaction(retries=10)
    def store_order(self, method, charge_result, userid, contact_info):
        """Store various data following payment processing.

        This code runs in a separate transaction (with up to 10 retries)
        to make sure that ConflictErrors do not cause the Zope publisher
        to retry the request which performs payment processing.

        # ^ is the above still true when using Authorize.Net SIM??

        IMPORTANT: Make sure that code which runs before this is called
        does not try to make persistent changes, because they'll be lost.
        """
        order = self.cart.data
        order['bill_to'] = contact_info
        order['notes'] = self.request.form.get('notes')

        # `success` is only present for purchases, not refunds
        if 'success' in charge_result and charge_result['success']:

            # Call `after_purchase` hook for each product
            coupons_used = set()
            for index, item in enumerate(self.cart.items):
                ob = resolve_uid(item.uid)
                if ob is not None:
                    purchase_handler = IPurchaseHandler(ob)
                    purchase_handler.after_purchase(item._item)

                # keep track of coupons used
                if item.is_discounted:
                    coupons_used.add(item.coupon)

            # store count of coupon usage
            for coupon_uid in coupons_used:
                storage.increment_shop_data(
                    [userid, 'coupons', coupon_uid], 1)

        # Store historic record of order
        self.cart.store_order(userid)

        # Keep cart as old_cart (for the thank you page) before clearing it
        self.old_cart = self.cart.clone()

        # Queue receipt email (email is actually sent at transaction commit)
        if self.receipt_email:
            subject = get_setting('receipt_subject')
            unstyled_msg = self.receipt_email()
            css = self.context.unrestrictedTraverse('plone.css')()
            # remove specific lines of css that were causing premailer to fail
            # due to:'unicodeescape' codec can't decode byte 0x5c in position 26
            # x--------------------------
            css_parsed = []
            for x in css.split("\n"):
                if '\.' not in x:
                    css_parsed.append(x)
            cssp = "".join(css_parsed)
            # x--------------------------
            msg = Premailer(unstyled_msg, css_text=cssp).transform()
            # only send email if the email field was entered in the SIM billing
            # address section and if the email address is a valid email format
            if 'x_email' in self.request.form:
                try:
                    is_email(self.request.form['x_email'])
                except Exception as e:
                    self.error = str(e)
                if not self.error:
                    mto = self.request['x_email']
                    send_mail(subject, msg, mto=mto)

    @run_in_transaction(retries=5)
    def clear_cart(self):
        """Clear the cart following checkout.

        This is done in a separate transaction so that a cart in the session
        is still intact in case `store_order` needs to be retried.
        """
        self.cart.clear()

    def receipt_intro(self):
        return get_setting('receipt_intro')


@implementer(IStripeEnabledView)
class CheckoutFormStripe(BrowserView):
    """ Renders a checkout form set up to submit through Stripe """

    cart_template = ViewPageTemplateFile('templates/checkout_cart.pt')
    thankyou_template = ViewPageTemplateFile('templates/checkout_thankyou.pt')
    receipt_email = ViewPageTemplateFile('templates/receipt_email.pt')
    index = ViewPageTemplateFile('templates/checkout_form.pt')

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @lazy_property
    def amount(self):
        return self.cart.amount

    def __call__(self):
        self.update()
        if 'submitted' in self.request.form:
            self.handle_submit()

        return self.render()

    def update(self):
        self.error = None
        self.prepopulate_billing_info()
        self.cart.calculate_taxes()
        # Make sure writing tax to cart doesn't trigger CSRF warning
        safeWrite(self.cart.data)

    def render(self):
        if 'submitted' in self.request.form and not self.error:
            return self.thankyou_template()
        else:
            return self.index()

    @lazy_property
    def countries(self):
        return country_names

    @lazy_property
    def years(self):
        year = date.today().year
        return range(year, year + 11)

    def prepopulate_billing_info(self):
        # Do we want to store contact info?
        # If so we can prefill the form by putting values
        # in the request here.
        pass

    def is_superuser(self):
        return has_permission('Manage portal')

    def handle_submit(self):
        amount = self.amount

        try:
            is_email(self.request.form['email'])
        except Exception as e:
            self.error = str(e)

        if self.cart.shippable and not self.cart.data.get('ship_method'):
            self.error = ('Something went wrong while calculating shipping. '
                          'Your payment has not been processed. '
                          'Please contact us for assistance.')

        if self.error:
            return

        userid = get_current_userid()
        contact_info = PersistentMapping()
        for f in ('first_name', 'last_name', 'email', 'phone', 'address',
                  'city', 'state', 'zip', 'country'):
            contact_info[f] = self.request.form[f]

        method = 'Online Payment'
        if self.is_superuser():
            method = self.request.form.get('method', 'None')
            if method not in ('Online Payment', 'Check', 'Cash', 'None'):
                raise Forbidden('Invalid payment method: %s' % method)
            if amount and (method == 'None'):
                raise Forbidden('Invalid payment method: None')

        charge_result = {'success': True}
        if amount and method == 'Online Payment':
            if 'stripeToken' not in self.request.form:
                self.error = 'Unable to process payment. Please try again.'
                return
            card_token = self.request.form['stripeToken']

            try:
                charge_result = process_interactive_payment(
                    self.cart, card_token, contact_info)
                charge_result['success'] = True
            except PaymentProcessingException as e:
                charge_result = {
                    'success': False,
                    'err_msg': e.message,
                    'err_code': getattr(e, 'code', None),
                }
                self.error = e.message

        if not self.error:
            try:
                self.store_order(method, charge_result, userid, contact_info)
                self.clear_cart()
            except ConflictError:
                raise Exception(
                    'Failed to store results of payment after multiple '
                    'retries. Please contact us for assistance.')

    # This code runs after the payment is processed
    # to update various data in the ZODB.
    @run_in_transaction(retries=10)
    def store_order(self, method, charge_result, userid, contact_info):
        """Store various data following payment processing.

        This code runs in a separate transaction (with up to 10 retries)
        to make sure that ConflictErrors do not cause the Zope publisher
        to retry the request which performs payment processing.

        IMPORTANT: Make sure that code which runs before this is called
        does not try to make persistent changes, because they'll be lost.
        """
        order = self.cart.data
        order['bill_to'] = contact_info
        order['notes'] = self.request.form.get('notes')
        if 'id' in charge_result:
            order['stripe_id'] = charge_result['id']
        if 'card' in charge_result:
            order['card_last4'] = charge_result['card']['last4']
            order['card_type'] = charge_result['card']['brand']
            order['card_exp'] = '{:02d}{:02d}'.format(
                charge_result['card']['exp_month'],
                charge_result['card']['exp_year'] % 100
            )

        if self.is_superuser():
            order['proxy_userid'] = self.request.SESSION.get('superuser')
            order['payment_method'] = method
            number = self.request.form.get('number')
            if number:
                if method == 'Check':
                    order['check_number'] = number
                else:
                    order['receipt_number'] = number

        # `success` is only present for purchases, not refunds
        if 'success' in charge_result and charge_result['success']:

            # Call `after_purchase` hook for each product
            coupons_used = set()
            for index, item in enumerate(self.cart.items):
                ob = resolve_uid(item.uid)
                if ob is not None:
                    purchase_handler = IPurchaseHandler(ob)
                    purchase_handler.after_purchase(item._item)

                # keep track of coupons used
                if item.is_discounted:
                    coupons_used.add(item.coupon)

            # store count of coupon usage
            for coupon_uid in coupons_used:
                storage.increment_shop_data(
                    [userid, 'coupons', coupon_uid], 1)

        # Store historic record of order
        self.cart.store_order(userid)

        # Keep cart as old_cart (for the thank you page) before clearing it
        self.old_cart = self.cart.clone()

        # Queue receipt email (email is actually sent at transaction commit)
        if self.receipt_email:
            subject = get_setting('receipt_subject')
            unstyled_msg = self.receipt_email()
            css = self.context.unrestrictedTraverse('plone.css')()
            msg = Premailer(unstyled_msg, css_text=css).transform()
            mto = self.request['email']
            send_mail(subject, msg, mto=mto)

    @run_in_transaction(retries=5)
    def clear_cart(self):
        """Clear the cart following checkout.

        This is done in a separate transaction so that a cart in the session
        is still intact in case `store_order` needs to be retried.
        """
        self.cart.clear()

    def receipt_intro(self):
        return get_setting('receipt_intro')

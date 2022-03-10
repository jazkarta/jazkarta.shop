import six
from AccessControl import getSecurityManager
from persistent.mapping import PersistentMapping
from ZODB.POSException import ConflictError
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zExceptions import Forbidden
from jazkarta.shop import config
from jazkarta.shop import storage
from . import CheckoutFormBase
from ...interfaces import IPurchaseHandler
from ...interfaces import PaymentProcessingException
from ...authnet import createTransactionRequest
from ...authnet import ARBCreateSubscriptionRequest
from ...utils import get_current_userid
from ...utils import get_setting
from ...utils import resolve_uid
from ...utils import run_in_transaction
from ...validators import is_email
import time


class CheckoutFormAuthorizeNetAcceptJs(CheckoutFormBase):
    """ Renders a checkout form set up to submit through Stripe """
    index = ViewPageTemplateFile(
        '../templates/checkout_form_authorize_net_accept_js.pt')

    @lazy_property
    def authorizenet_production(self):
        return config.IN_PRODUCTION

    @lazy_property
    def authorizenet_client_key(self):
        if self.authorizenet_production:
            return get_setting('authorizenet_client_key_production')
        else:
            return get_setting('authorizenet_client_key_dev')

    @lazy_property
    def authorizenet_api_login_id(self):
        if self.authorizenet_production:
            return get_setting('authorizenet_api_login_id_production')
        else:
            return get_setting('authorizenet_api_login_id_dev')

    @lazy_property
    def refId(self):
        return six.text_type(time.time())

    capture_payment = True
    is_recurring = False
    recurring_months = None

    def handle_submit(self):
        if not len(self.cart.items):
            self.error = 'There is nothing in your cart.'
            return
        amount = self.amount

        try:
            is_email(self.request.form['email'])
        except Exception as e:
            self.error = six.text_type(e)

        if self.cart.shippable and not self.cart.data.get('ship_method'):
            self.error = ('Something went wrong while calculating shipping. '
                          'Your payment has not been processed. '
                          'Please contact us for assistance.')

        if self.error:
            return

        userid = get_current_userid()
        contact_info = PersistentMapping()
        for f in (
                'name_on_card', 'email', 'phone', 'address', 'city', 'state',
                'zip', 'country'):
            if f in self.request.form:
                contact_info[f] = self.request.form[f]
        if 'name_on_card' in contact_info:
            names = contact_info['name_on_card'].split()
            contact_info['first_name'] = u' '.join(names[:-1])
            contact_info['last_name'] = names[-1]

        method = 'Online Payment'
        if self.is_superuser():
            method = self.request.form.get('method', 'None')
            if method not in ('Online Payment', 'Check', 'Cash', 'None'):
                raise Forbidden('Invalid payment method: %s' % method)
            if amount and (method == 'None'):
                raise Forbidden('Invalid payment method: None')

        response = None
        if amount and method == 'Online Payment':
            if ('dataDescriptor' not in self.request.form or
                    'dataValue' not in self.request.form):
                self.error = 'Unable to process payment. Please try again.'
                return

            opaque_data = {
                'dataDescriptor': self.request.form['dataDescriptor'],
                'dataValue': self.request.form['dataValue'],
            }

            try:
                if self.is_recurring:
                    response = ARBCreateSubscriptionRequest(
                        self.cart, self.refId, opaque_data, contact_info,
                        months=self.recurring_months)
                else:
                    transactionType = (
                        'authCaptureTransaction' if self.capture_payment
                        else 'authOnlyTransaction'
                    )
                    response = createTransactionRequest(
                        self.cart, self.refId, opaque_data, contact_info,
                        transactionType=transactionType)
            except PaymentProcessingException as e:
                self.error = e.message

        if not self.error:
            try:
                self.store_order(method, response, userid, contact_info)
                self.notify_purchased()
                self.clear_cart()
            except ConflictError:
                self.error = ('Failed to store results of payment after '
                              'multiple retries. Please contact us for '
                              'assistance. ')

    # This code runs after the payment is processed
    # to update various data in the ZODB.
    @run_in_transaction(retries=10)
    def store_order(self, method, response, userid, contact_info):
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
        if response is not None:
            if self.is_recurring:
                order['authorizenet_transaction_id'] = six.text_type(
                    response.subscriptionId
                )
            else:
                order['authorizenet_transaction_id'] = six.text_type(
                    response.transactionResponse.transId
                )
                order['card_last4'] = response.transactionResponse.accountNumber[-4:]
                order['card_type'] = response.transactionResponse.accountType

        if self.is_superuser():
            order['proxy_userid'] = getSecurityManager().getUser().getId()
            order['payment_method'] = method
            number = self.request.form.get('number')
            if number:
                if method == 'Check':
                    order['check_number'] = number
                else:
                    order['receipt_number'] = number

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
        self.order_id = self.cart.store_order(userid)

        # Keep cart as old_cart (for the thank you page) before clearing it
        self.old_cart = self.cart.clone()

        self.send_receipt_email()

import six
from AccessControl import getSecurityManager
from persistent.mapping import PersistentMapping
from ZODB.POSException import ConflictError
from zope.browserpage import ViewPageTemplateFile
from zope.interface import implementer
from zExceptions import Forbidden
from jazkarta.shop import storage
from . import CheckoutFormBase
from ...interfaces import IPurchaseHandler
from ...interfaces import IStripeEnabledView
from ...interfaces import PaymentProcessingException
from ...stripe import process_interactive_payment
from ...utils import get_current_userid
from ...utils import resolve_uid
from ...utils import run_in_transaction
from ...validators import is_email


@implementer(IStripeEnabledView)
class CheckoutFormStripe(CheckoutFormBase):
    """ Renders a checkout form set up to submit through Stripe """
    index = ViewPageTemplateFile('../templates/checkout_form_stripe.pt')

    def handle_submit(self):
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
                self.notify_purchased()
                self.clear_cart()
            except ConflictError:
                    self.error = ('Failed to store results of payment after '
                                  'multiple retries. Please contact us for '
                                  'assistance. ')

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
        elif 'payment_method_details' in charge_result: # stripe api v2
            paymentdetails = charge_result['payment_method_details']
            if 'card' in paymentdetails:
                order['card_last4'] = paymentdetails['card']['last4']
                order['card_type'] = paymentdetails['card']['brand']
                order['card_exp'] = '{:02d}{:02d}'.format(
                    paymentdetails['card']['exp_month'],
                    paymentdetails['card']['exp_year'] % 100
                )

        if self.is_superuser():
            order['proxy_userid'] = getSecurityManager().getUser().getId()
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
        self.order_id = self.cart.store_order(userid)

        # Keep cart as old_cart (for the thank you page) before clearing it
        self.old_cart = self.cart.clone()

        self.send_receipt_email()

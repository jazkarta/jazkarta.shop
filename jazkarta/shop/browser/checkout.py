from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
from datetime import date
from persistent.mapping import PersistentMapping
from plone.protect.utils import safeWrite
from premailer import Premailer
from Products.Five import BrowserView
from ZODB.POSException import ConflictError
from zope.browserpage import ViewPageTemplateFile
from zope.cachedescriptors.property import Lazy as lazy_property
from zope.interface import implementer
from zExceptions import Forbidden
from jazkarta.shop import storage
from ..cart import Cart
from ..interfaces import IPurchaseHandler
from ..interfaces import IStripeEnabledView
from ..interfaces import PaymentProcessingException
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
    index = ViewPageTemplateFile('templates/checkout_form_authorize_net_sim.pt')
    post_url = 'https://accept.authorize.net/payment/payment'

    @lazy_property
    def cart(self):
        return Cart.from_request(self.request)

    @lazy_property
    def amount(self):
        return self.cart.amount

    def token(self):

        merchantAuth = apicontractsv1.merchantAuthenticationType()
        merchantAuth.name = get_setting('authorizenet_api_login_id_dev')
        merchantAuth.transactionKey = get_setting('authorizenet_transaction_key_dev')
        
        setting1 = apicontractsv1.settingType()
        setting1.settingName = apicontractsv1.settingNameEnum.hostedPaymentButtonOptions
        setting1.settingValue = "{\"text\": \"Pay\"}"

        setting2 = apicontractsv1.settingType()
        setting2.settingName = apicontractsv1.settingNameEnum.hostedPaymentOrderOptions
        setting2.settingValue = "{\"show\": false}"
        
        settings = apicontractsv1.ArrayOfSetting()
        settings.setting.append(setting1)
        settings.setting.append(setting2)
        
        transactionrequest = apicontractsv1.transactionRequestType()
        transactionrequest.transactionType = "authCaptureTransaction"
        transactionrequest.amount = self.amount

        paymentPageRequest = apicontractsv1.getHostedPaymentPageRequest()
        paymentPageRequest.merchantAuthentication = merchantAuth
        paymentPageRequest.transactionRequest = transactionrequest
        paymentPageRequest.hostedPaymentSettings = settings

        paymentPageController = getHostedPaymentPageController(paymentPageRequest)
        paymentPageController.execute()
        paymentPageResponse = paymentPageController.getresponse()

        if paymentPageResponse is not None:
            ok = apicontractsv1.messageTypeEnum.Ok
            if paymentPageResponse.messages.resultCode == ok:
		        print('Successfully got hosted payment page!')

		        print('Token : %s' % paymentPageResponse.token)

		        if paymentPageResponse.messages:
			        print('Message Code : %s' % \
                    paymentPageResponse.messages.message[0]['code'].text)
			        print('Message Text : %s' % \
                    paymentPageResponse.messages.message[0]['text'].text)
            else:
                if paymentPageResponse.messages:
                    print('Failed to get batch statistics.\nCode:%s \nText:%s'%\
                    (paymentPageResponse.messages.message[0]['code'].text,
                     paymentPageResponse.messages.message[0]['text'].text))

        return paymentPageResponse.token

    def __call__(self):
        return self.render()

    def render(self):
        return self.index()


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

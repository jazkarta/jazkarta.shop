import logging
import six

from authorizenet import apicontractsv1
from authorizenet.constants import constants
from authorizenet.apicontrollers import createTransactionController
from authorizenet.apicontrollers import ARBCreateSubscriptionController
from contextlib import contextmanager
from datetime import date

from . import config
from .interfaces import PaymentProcessingException
from .utils import get_setting


class AuthorizeDotNetDebugFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.DEBUG:
            record.levelno = logging.WARNING
            return 1
        else:
            return 0


logger = logging.getLogger(__name__)
authnet_logger = logging.getLogger(constants.defaultLoggerName)
authnet_logger.addHandler(logging.StreamHandler())
authnet_debugfilter = AuthorizeDotNetDebugFilter()


@contextmanager
def enhanced_authnet_logging():
    """Boost authorizenet's own logging so we can get a better view
    into what's happening during transaction processing.
    """
    # Bump up the logging
    authnet_logger.setLevel(logging.DEBUG)
    authnet_logger.addFilter(authnet_debugfilter)

    yield

    # Ratchet it down again
    authnet_logger.setLevel(logging.CRITICAL)
    authnet_logger.removeFilter(authnet_debugfilter)


def _getMerchantAuth():
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    if config.IN_PRODUCTION:
        merchantAuth.name = get_setting('authorizenet_api_login_id_production')
        merchantAuth.transactionKey = get_setting(
            'authorizenet_transaction_key_production')
    else:
        merchantAuth.name = get_setting('authorizenet_api_login_id_dev')
        merchantAuth.transactionKey = get_setting(
            'authorizenet_transaction_key_dev')
    return merchantAuth


def _getPayment(opaque_data):
    # Create the payment object for a payment nonce
    opaqueData = apicontractsv1.opaqueDataType()
    opaqueData.dataDescriptor = opaque_data['dataDescriptor']
    opaqueData.dataValue = opaque_data['dataValue']

    # Add the payment data to a paymentType object
    payment = apicontractsv1.paymentType()
    payment.opaqueData = opaqueData
    return payment


def _getLineItems(cart):
    line_items = apicontractsv1.ArrayOfLineItem()
    for item in cart.items:
        line_item = apicontractsv1.lineItemType()
        line_item.itemId = item.uid[:31]
        line_item.name = item.category
        line_item.description = item.name[:255]
        line_item.quantity = six.text_type(item.quantity)
        line_item.unitPrice = six.text_type(item.price)
        line_items.lineItem.append(line_item)
    return line_items


def createTransactionRequest(
        cart, refId, opaque_data, contact_info,
        transactionType='authCaptureTransaction'):

    # Get Authorize.net API credentials
    merchantAuth = _getMerchantAuth()

    # Get payment info
    payment = _getPayment(opaque_data)

    # Create order information
    order = apicontractsv1.orderType()
    order.description = refId

    # Set the customer's Bill To address
    customerAddress = apicontractsv1.customerAddressType()
    customerAddress.firstName = contact_info.get(
        'first_name', contact_info.get('name_on_card', ''))
    customerAddress.lastName = contact_info.get('last_name', '')
    customerAddress.address = contact_info['address']
    customerAddress.city = contact_info['city']
    customerAddress.state = contact_info['state']
    customerAddress.zip = contact_info['zip']
    customerAddress.country = contact_info['country']
    customerAddress.phoneNumber = contact_info['phone']

    # Set the customer's identifying information
    customerData = apicontractsv1.customerDataType()
    customerData.type = "individual"
    customerData.email = contact_info['email']

    # @@@ shipping

    # Add values for transaction settings
    duplicateWindowSetting = apicontractsv1.settingType()
    duplicateWindowSetting.settingName = "duplicateWindow"
    duplicateWindowSetting.settingValue = "600"
    settings = apicontractsv1.ArrayOfSetting()
    settings.setting.append(duplicateWindowSetting)

    # Create a transactionRequestType object and add the previous objects to it
    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = transactionType
    transactionrequest.amount = six.text_type(cart.amount)
    transactionrequest.order = order
    transactionrequest.payment = payment
    transactionrequest.billTo = customerAddress
    transactionrequest.customer = customerData
    transactionrequest.transactionSettings = settings
    transactionrequest.lineItems = _getLineItems(cart)

    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.transactionRequest = transactionrequest

    with enhanced_authnet_logging():
        controller = createTransactionController(createtransactionrequest)
        if config.IN_PRODUCTION:
            controller.setenvironment(constants.PRODUCTION)
        controller.execute()
        response = controller.getresponse()

    logger.info(
        'createTransactionController response: {}'.format(response.__repr__())
    )
    defaultMsg = 'Your card could not be processed.'
    if controller._httpResponse:
        logger.info('Authorize.net response: {}'.format(controller._httpResponse))
    if response.messages.resultCode == 'Ok':
        if response.transactionResponse.responseCode != 1:  # Approved
            raise PaymentProcessingException(defaultMsg)
        return response
    else:
        raise PaymentProcessingException(
            response.messages.message[0].text or defaultMsg)


def ARBCreateSubscriptionRequest(
        cart, refId, opaque_data, contact_info, months):

    # Get Authorize.net API credentials
    merchantAuth = _getMerchantAuth()

    # Setting payment schedule
    paymentschedule = apicontractsv1.paymentScheduleType()
    paymentschedule.interval = apicontractsv1.paymentScheduleTypeInterval()
    paymentschedule.interval.length = 1
    paymentschedule.interval.unit = apicontractsv1.ARBSubscriptionUnitEnum.months
    paymentschedule.startDate = date.today()
    paymentschedule.totalOccurrences = months

    # Get payment info
    payment = _getPayment(opaque_data)

    # Create order information
    order = apicontractsv1.orderType()
    order.description = refId

    # Setting billing information
    billto = apicontractsv1.nameAndAddressType()
    billto.firstName = contact_info['first_name']
    billto.lastName = contact_info['last_name']
    billto.address = contact_info['address']
    billto.city = contact_info['city']
    billto.state = contact_info['state']
    billto.zip = contact_info['zip']
    billto.country = contact_info['country']
    billto.phoneNumber = contact_info['phone']

    # Set the customer's identifying information
    customerData = apicontractsv1.customerType()
    customerData.type = "individual"
    customerData.email = contact_info['email']
    customerData.phoneNumber = contact_info['phone']

    # Setting subscription details
    subscription = apicontractsv1.ARBSubscriptionType()
    subscription.paymentSchedule = paymentschedule
    subscription.amount = six.text_type(cart.amount)
    subscription.order = order
    subscription.customer = customerData
    subscription.billTo = billto
    subscription.payment = payment

    # Creating the request
    request = apicontractsv1.ARBCreateSubscriptionRequest()
    request.merchantAuthentication = merchantAuth
    request.subscription = subscription

    with enhanced_authnet_logging():
        controller = ARBCreateSubscriptionController(request)
        if config.IN_PRODUCTION:
            controller.setenvironment(constants.PRODUCTION)
        controller.execute()
        response = controller.getresponse()

    logger.info(
        'ARBCreateSubscriptionController response: {}'.format(response.__repr__())
    )
    if response.messages.resultCode == 'Ok':
        return response
    else:
        raise PaymentProcessingException(response.messages.message[0].text)

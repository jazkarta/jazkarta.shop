from authorizenet import apicontractsv1
from authorizenet import constants
from authorizenet.apicontrollers import createTransactionController
from . import config
from .interfaces import PaymentProcessingException
from .utils import get_setting


def createTransactionRequest(cart, refId, opaque_data, contact_info):
    # Create a merchantAuthenticationType object with authentication details
    # retrieved from the constants file
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    if config.IN_PRODUCTION:
        merchantAuth.name = get_setting('authorizenet_api_login_id_production')
        merchantAuth.transactionKey = get_setting(
            'authorizenet_transaction_key_production')
    else:
        merchantAuth.name = get_setting('authorizenet_api_login_id_dev')
        merchantAuth.transactionKey = get_setting(
            'authorizenet_transaction_key_dev')

    # Create the payment object for a payment nonce
    opaqueData = apicontractsv1.opaqueDataType()
    opaqueData.dataDescriptor = opaque_data['dataDescriptor']
    opaqueData.dataValue = opaque_data['dataValue']

    # Add the payment data to a paymentType object
    paymentOne = apicontractsv1.paymentType()
    paymentOne.opaqueData = opaqueData

    # Create order information
    order = apicontractsv1.orderType()
    order.description = refId

    # @@@ send individual line items

    # Set the customer's Bill To address
    customerAddress = apicontractsv1.customerAddressType()
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
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = str(cart.amount)
    transactionrequest.order = order
    transactionrequest.payment = paymentOne
    transactionrequest.billTo = customerAddress
    transactionrequest.customer = customerData
    transactionrequest.transactionSettings = settings

    # Assemble the complete transaction request
    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.transactionRequest = transactionrequest

    # Create the controller and get response
    createtransactioncontroller = createTransactionController(
        createtransactionrequest)
    if config.IN_PRODUCTION:
        createtransactioncontroller.setenvironment(constants.PRODUCTION)
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()
    if response.messages.resultCode == 'Ok':
        if response.transactionResponse.responseCode != 1:  # Approved
            raise PaymentProcessingException('Your card could not be processed.')
        return response
    else:
        raise PaymentProcessingException(response.messages.message[0].text)

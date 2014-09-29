from billing import Integration, get_gateway, IntegrationNotConfigured
from billing.gateways.eway_gateway.rapidapi.rapid import RapidAPI
from billing.forms.eway_au_forms import EwayAuForm
from django.conf import settings
from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt
import operator

translation = {
    'SaveToken': 'save_token',
    'TokenCustomerID': 'token_customer_id',
    'Reference': 'reference',
    'Title': 'title',
    'FirstName': 'first_name',
    'LastName': 'last_name',
    'CompanyName': 'company',
    'JobDescription': 'job',
    'Street1': 'street',
    'City': 'city',
    'State': 'state',
    'PostalCode': 'postal_code',
    'Country': 'country',
    'Email': 'email',
    'Phone': 'phone',
    'Mobile': 'mobile',
    'Comments': 'comments',
    'Fax': 'fax',
    'Url': 'url',
    'CardNumber': 'card_number',
    'CardName': 'card_name',
    'CardExpiryMonth': 'card_expiry_month',
    'CardExpiryYear': 'card_expiry_year',
    'Option1': 'option_1',
    'Option2': 'option_2',
    'Option3': 'option_3',
    'BeagleScore': 'beagle_score',
    'ErrorMessage': 'error_message',
    'TransactionStatus': 'transaction_status',
    'TransactionID': 'transaction_id',
    'TotalAmount': 'total_amount',
    'InvoiceReference': 'invoice_reference',
    'InvoiceNumber': 'invoice_number',
    'ResponseCode': 'response_code',
    'ResponseMessage': 'response_message',
    'AuthorisationCode': 'authorisation_code',
    'AccessCode': 'access_code',
}
translation.update(dict(zip(translation.values(), translation.keys())))


def translate(original):
    """
    Translate between the eWAY SOAP naming convention (camel case), and
    Python's convention (lowercase separated with underscores).

    Takes and returns a dictionary.

    Untranslatable keys are not included in returned dict.
    """
    translated = {}
    for k, v in translation.items():
        try:
            value = original[k]
        except KeyError:
            continue
        translated[v] = value
    return translated


def attr_update(object_, dict_):
    for k, v in dict_.items():
        setattr(object_, k, v)

class EwayRapidIntegration(Integration):
    display_name = "eWAY Rapid v3"
    service_url = "https://au.ewaygateway.com/mh/payment"
    template = "billing/eway_api.html"
    urls = ()

    def __init__(self, access_code=None):
        super(EwayRapidIntegration, self).__init__()
        merchant_settings = getattr(settings, "MERCHANT_SETTINGS")
        if not merchant_settings or not merchant_settings.get("eway_rapid"):
            raise IntegrationNotConfigured("The '%s' integration is not correctly "
                                           "configured." % self.display_name)
        eway_settings = merchant_settings["eway_rapid"]
        self.customer_id = eway_settings["CUSTOMER_ID"]
        self.username = eway_settings["USERNAME"]
        self.password = eway_settings["PASSWORD"]
        self.sandbox = eway_settings["SANDBOX"]
        self.debug = eway_settings["DEBUG"]
        # Don't use X-Forwarded-For. It doesn't really matter if REMOTE_ADDR
        # isn't their *real* IP, we're only interested in what IP they're going
        # to use for their POST request to eWAY. If they're using a proxy to
        # connect to us, it's fair to assume they'll use the same proxy to
        # connect to eWAY.
        self.access_code = access_code

    def generate_form(self):
        initial_data = dict(EWAY_ACCESSCODE=self.access_code, **self.fields)
        return EwayAuForm(initial=initial_data)

    def request_access_code(self, payment, return_url, customer=None,
                            billing_country=None, shipping={}, ip_address=None):
        # # enforce required fields
        assert self.username
        assert self.password
        assert payment['total_amount']
        assert return_url
        # # turn customer to dict
        # customer_echo = dict(((k, getattr(response.Customer, k))
        #                       for k in dir(response.Customer)))
        rapid = RapidAPI(api_method='REST', api_format='JSON', username=self.username, password=self.password, debug=self.debug, sandbox=self.sandbox)
        req = {
            'Customer': customer,
            'ShippingAddress': shipping,
            'Options': [],
            'Items': payment.get('items', []),
            'Payment': {
                'TotalAmount': payment['total_amount'] * 100,
                'InvoiceNumber': payment['order_id'],
                'InvoiceDescription': '',
                'InvoiceReference': '',
                'CurrencyCode': payment.get('currency', 'AUD'),
            },
            # Url to the page for getting the result with an AccessCode
            # Note: RedirectUrl is a Required Field For all cases
            'RedirectUrl': return_url,
            'Method': 'TokenPayment', #data.get('ddlMethod'),
            'CustomerIP': ip_address or ''
        }
        result = rapid.create_access_code(req)[0]
        self.access_code = result['AccessCode']
        self.service_url = result['FormActionURL']
        # return (self.access_code, translate(customer_echo))
        # customer_echo = dict(((k, getattr(result['Customer'], k))
        #                               for k in dir(response.Customer)))
        #translate(result['Customer'])
        return (self.access_code, translate(result['Customer']), result)

    def check_transaction(self):
        if not self.access_code:
            raise ValueError("`access_code` must be specified")
        rapid = RapidAPI(api_method='REST', api_format='JSON', username=self.username, password=self.password, debug=self.debug, sandbox=self.sandbox)
        result = rapid.get_access_code({'AccessCode': self.access_code})[0]
        options = result.get('Options')
        data = {
            'AccessCode': self.access_code,
            'AuthorisationCode': result.get('AuthorisationCode'),
            'InvoiceNumber': result.get('InvoiceNumber'),
            'InvoiceReference': result.get('InvoiceReference'),
            'ResponseCode': result.get('ResponseCode'),
            'ResponseMessage': result.get('ResponseMessage'),
            'TokenCustomerID': result.get('TokenCustomerID'),
            'TotalAmount': result.get('TotalAmount'),
            'TransactionID': result.get('TransactionID'),
            'TransactionStatus': result.get('TransactionStatus'),
            'BeagleScore': result.get('BeagleScore'),
        }
        return translate(data)
        # return translate(dict(((k, getattr(response, k)) for k in dir(response))))

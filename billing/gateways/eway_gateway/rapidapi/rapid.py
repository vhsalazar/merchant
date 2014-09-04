#-*- coding:utf-8 -*-
# import urllib
import urllib2
import base64
import logging

import parser

from httplib import BadStatusLine
from urllib2 import HTTPError
from suds.client import Client
from suds.transport.https import HttpAuthenticated


class RapidAPIError(Exception):
    def __init__(self, result):
        Exception.__init__(self, self.message)

class RapidAPI(object):
    def __init__(self, api_method='', api_format='', username=None, password=None, debug=False, sandbox=True):
        if not api_method or not api_format:
            error = 'Method' if not self.method else ''
            error += ', Format' if not self.format else ''
            raise RapidAPIError('Initial data Error: %s unset' % (error))

        self.method = api_method.upper()
        self.format = api_format.upper()

        if not username and not password:
            error = 'Username' if not username else ''
            error += ', Password' if not password else ''
            raise RapidAPIError('Initial data Error: %s unset' % (error))

        self.username = username
        self.password = password

        self.debug = debug

        # Set URL endpoints
        # For RestURL need:
        # /AccessCodes  if CreateAccessCode action
        # /AccessCode/{AccessCode} if GetAccessCode action
        if sandbox:
            self.url = {
                'SOAP': 'https://api.sandbox.ewaypayments.com/soap.asmx',
                'REST': 'https://api.sandbox.ewaypayments.com/AccessCode',
                'POST': {
                    'XML': {
                        'CREATE': 'https://api.sandbox.ewaypayments.com/CreateAccessCode.xml',
                        'GET': 'https://api.sandbox.ewaypayments.com/GetAccessCodeResult.xml'
                    },
                    'JSON': {
                        'CREATE': 'https://api.sandbox.ewaypayments.com/CreateAccessCode.json',
                        'GET': 'https://api.sandbox.ewaypayments.com/GetAccessCodeResult.json'
                    }
                },
                'RPC': {
                    'XML': 'https://api.sandbox.ewaypayments.com/xml-rpc',
                    'JSON': 'https://api.sandbox.ewaypayments.com/json-rpc'
                }
            }
        else:
            self.url = {
                'SOAP': 'https://api.ewaypayments.com/soap.asmx',
                'REST': 'https://api.ewaypayments.com/AccessCode',
                'POST': {
                    'XML': {
                        'CREATE': 'https://api.ewaypayments.com/CreateAccessCode.xml',
                        'GET': 'https://api.ewaypayments.com/GetAccessCodeResult.xml'
                    },
                    'JSON': {
                        'CREATE': 'https://api.ewaypayments.com/CreateAccessCode.json',
                        'GET': 'https://api.ewaypayments.com/GetAccessCodeResult.json'
                    }
                },
                'RPC': {
                    'XML': 'https://api.ewaypayments.com/xml-rpc',
                    'JSON': 'https://api.ewaypayments.com/json-rpc'
                }
            }

    def __var_dump__(self, msg, var):
        if self.debug:
            print '------------------------'
            print msg + '\t' + str(var)
            print '------------------------'

    def _convert_object_(self, obj, action=''):
        """ Convert An Object to Target Formats """

        if self.method == 'RPC' and action == '':
            raise RapidAPIError('Internal Error: no action for RPC call')

        if self.method == 'SOAP':
            items = obj.get('Items')
            if items:
                obj['Items'] = {'LineItem': items}
            result =  parser.options_to_xml(obj)
        else:
            if self.format == 'XML':
                if self.method == 'RPC':
                    result = parser.object_to_rpcxml(action, obj)
                else:
                    if obj.get('AccessCode'):
                        # If GetAccessCode
                        result = parser.object_to_xml(obj, False)
                    else:
                        result = parser.object_to_xml(obj)
            else:
                if self.method == 'RPC':
                    result = parser.object_to_jsonrpc(action, obj)
                else:
                    result = parser.object_to_json(obj)
        return result

    def _convert_response_(self, resp):
        """ Convert From Target Format to Target Object """

        if self.method == 'SOAP':
            result = parser.instance_to_object(resp)
            access_code = result.get('AccessCode')
        else:
            if self.format == 'XML':
                if self.method == 'RPC':
                    result, access_code = parser.rpcxml_to_object(resp)
                else:
                    result, access_code = parser.xml_to_object(resp)
            else:
                if self.method == 'RPC':
                    result, access_code = parser.jsonrpc_to_object(resp)
                else:
                    result, access_code = parser.json_to_object(resp)

        return result, access_code


    def _access_code_method_(self, request, action, access_code='', is_post=True):
        result = None
        if self.method == 'SOAP':

            if self.debug:
                logging.basicConfig(level=logging.DEBUG)
                logging.getLogger('suds.client').setLevel(logging.DEBUG)
            else:
                logging.basicConfig(level=logging.INFO)
                logging.getLogger('suds.client').setLevel(logging.INFO)

            # Create AUTH credentials
            credentials = dict(username=self.username, password=self.password)
            t = HttpAuthenticated(**credentials)

            # Read WSDL
            wsdl_url = '%s?WSDL' % self.url['SOAP']
            client = Client(wsdl_url, transport=t)

            # Send request
            if action == 'CREATE':
                result = client.service.CreateAccessCode(request)
            else:
                result = client.service.GetAccessCodeResult(request)

        elif self.method == 'REST':
            # Create URL for REST
            rest_url = self.url['REST']
            rest_url += 's' if action == 'CREATE' else '/%s' % str(access_code)
            result = self.__post_to_rapidapi__(rest_url, request, is_post)

        elif self.method == 'POST':
            is_post = True
            if self.format == 'XML':
                result = self.__post_to_rapidapi__(self.url['POST']['XML'][action], request, is_post)
            else:
                result = self.__post_to_rapidapi__(self.url['POST']['JSON'][action], request, is_post)

        elif self.method == 'RPC':
            if self.format == 'XML':
                result = self.__post_to_rapidapi__(self.url['RPC']['XML'], request, is_post)
            else:
                result = self.__post_to_rapidapi__(self.url['RPC']['JSON'], request, is_post)

        return result


    def create_access_code(self, request):
        """
        Create access code based on method & format settings

        :param request: object
        :return: object
        """
        self.__var_dump__('CreateAccessCode Request object (origin):', request)

        # Convert request object to target format
        request = self._convert_object_(request, 'CreateAccessCode')

        self.__var_dump__('CreateAccessCode Request object (converted to format):', request)

        # Get response via creating access code by self.method
        response = self._access_code_method_(request, 'CREATE')

        if response == None:
            raise RapidAPIError('CreateAccessCode Internal Error: No response')

        self.__var_dump__('CreateAccessCode Response object:', response)

        # Convert response back to object
        result, access_code = self._convert_response_(response)

        self.__var_dump__('CreateAccessCode Result object: ', result)

        return result, access_code

    def get_access_code(self, request):
        """
        :param request: GetAccessCodeRequest instanse
        :return: object
        """

        self.__var_dump__('Get access code Request object (origin):', request)

        # Convert request object to target format
        access_code = request.get('AccessCode')
        request = self._convert_object_(request, 'GetAccessCodeResult')

        self.__var_dump__('Get access code Request object (converted): ', request)

        # Call the method
        response = self._access_code_method_(request, 'GET', access_code, False)

        if not response:
            raise RapidAPIError('GetAccessCode Internal Error: No response')

        self.__var_dump__('Get access code Response object:', response)

        # Convert Response Back TO An Object
        result = self._convert_response_(response)

        self.__var_dump__('GetAccessCodeResult Response object: ', result)

        return result

    def __post_to_rapidapi__(self, url, request_data, is_post):
        """
        Send data via POST/GET to URL
        :params:
            url = URL where to Send
            request_data = data for POST/GET message
            is_post = If True then POST else GET

        :return: Fetched result of response
        """

        self.__var_dump__("URL = ", url)
        # Create request instance
        request = urllib2.Request(url)

        # Create authentification header data for Request
        auth_header = '%s:%s' % (self.username, self.password)
        b64 = 'Basic %s' % base64.encodestring(auth_header).replace('\n', '')
        request.add_header('Authorization', b64)
        
        # Create content type header data for Request
        if self.format == 'XML':
            request.add_header('Content-type', 'application/xml')
        else:
            request.add_header('Content-type', 'application/json')

        # Calculate content size
        #request.add_header('Content-length', '%d' % len(request_data))

        if is_post:
            request.add_data(request_data)

        try:
            response = urllib2.urlopen(request)
            result = response.read()
            response.close()
        except HTTPError, err:
            print "HTTPError Code: %s Message: %s" % (err.code, err.message)
            result = None
        except BadStatusLine, err:
            print err

        return result

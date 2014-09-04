#-*- coding:utf-8 -*-
import xmlrpclib
from json import dumps, loads
from lxml import etree
from suds.sax.text import Text

# object -> ? parse methods
def object_to_json(request):
    return dumps(request)

def object_to_jsonrpc(action, request):
    if action == 'CreateAccessCode':
        # Tweak the request object in order to generate a valid JSON-RPC format for RapidAPI.
        if request.has_key('Payment') and request['Payment']:
            if request['Payment'].has_key('TotalAmount'):
                request['Payment']['TotalAmount'] = int(request['Payment']['TotalAmount'])

    data = {
        'id': 3,
        'method': action,
        'params': {
            'request': request,
        }
    }

    return dumps(data)

def options_to_xml(obj):
    # Change Options -> Value to Options -> Option -> Value
    options = []
    if obj.get('Options'):
        for option in obj['Options']:
            options.append({
                'Option': {
                    'Value': option.get('Value')
                },
            })
        obj['Options'] = options
    return obj

def items_to_xml(obj):
    items = []
    if obj.get('Items'):
        for item in obj['Items']:
            items.append({
                'ListItem': item,
            })
        obj['Items'] = items
    return obj

def object_to_xml(request, is_create=True):
    request = options_to_xml(request)
    request = items_to_xml(request)
    # Create XML document
    root_str = 'CreateAccessCodeRequest' if is_create else 'GetAccessCodeRequest'
    doc = etree.Element(root_str)
    get_object_xml(doc, request)
    return etree.tostring(doc)

def object_to_rpcxml(action, request, is_create=True):
    params = (request, )
    rpcxml = xmlrpclib.dumps(params, action)
    return rpcxml

def get_object_xml(node, obj):
    for item in obj:
        if obj[item]:
            child = etree.Element(str(item))
            if isinstance(obj[item], (str, unicode)):
                child.text = str(obj[item])
            else:
                if isinstance(obj[item], list):
                    for i in obj[item]:
                        get_object_xml(child, i)
                else:
                    get_object_xml(child, obj[item])
        node.append(child)

# ? -> object parse methods
def json_to_object(response):
    data = loads(response)
    return data, data.get('AccessCode')

def jsonrpc_to_object(response):
    data = loads(response)

    if data:
        errors = data.get('result').get('Errors')
        if errors:
            return dict('Errors', errors)

        return data.get('result'), data.get('result').get('AccessCode')
    else:
        return response, ''

def xml_to_object(response):    
    doc = etree.fromstring(response)
    # Parse XML document
    data = {}
    childs = doc.getchildren()
    for element in childs:
        tag, text = get_xml_to_object(element)
        data[tag] = text

    # Change Options -> Option -> Value to Options -> Value
    options = []
    if data.get('Options'):
        for option in data.get('Options'):
            value = data.get('Options').get(option)
            options.append({'Value': value.get('Value')})
    data['Options'] = options
    return data, data.get('AccessCode')

def get_xml_to_object(element):
    return element.tag, dict(map(get_xml_to_object, element)) or element.text or ''


def rpcxml_to_object(response):
    data = xmlrpclib.loads(response)[0][0]
    return data, data.get('AccessCode')

def instance_to_object(response):
    if response:
        data = {}
        for item in response:
            key = item[0]
            if len(item) > 1:
                if isinstance(item[1], Text):
                    value = item[1]
                else:
                    value = instance_to_object(item[1])
                data[key] = value
        return data
    return ''
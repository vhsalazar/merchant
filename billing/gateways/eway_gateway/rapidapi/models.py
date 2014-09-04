#-*- coding:utf-8 -*-
"""
    Models for RapidAPI
"""

class Customer(object):
    def __init__(self):
        # self.TokenCustomerID = ''
        self.Reference = ''
        self.Title = ''
        self.FirstName = ''
        self.LastName = ''
        self.CompanyName = ''
        self.JobDescription = ''
        self.Street1 = ''
        self.Street2 = ''
        self.City = ''
        self.State = ''
        self.PostalCode = ''
        self.Country = ''
        self.Email = ''
        self.Phone = ''
        self.Mobile = ''
        self.Comments = ''
        self.Fax = ''
        self.Url = ''

    def get_customer(self):
        return self.__dict__

class ShippingAddress(object):
    def __init__(self, data):
        self.FirstName = data.get('FirstName')
        self.LastName = data.get('LastName')
        self.Street1 = data.get('Street1')
        self.Street2 = data.get('Street2')
        self.City = data.get('City')
        self.State = data.get('State')
        self.Country = data.get('Country')
        self.PostalCode = data.get('PostalCode')
        self.Email = data.get('Email')
        self.Phone = data.get('Phone')
        self.ShippingMethod = data.get('ShippingMethod')

    def get_shipping_address(self):
        return self.__dict__

class Payment(object):
    def __init__(self, data):
        self.TotalAmount = data.get('TotalAmount')
        self.InvoiceNumber = data.get('InvoiceNumber')
        self.InvoiceDescription = data.get('InvoiceDescription')
        self.InvoiceDeference = data.get('InvoiceReference')
        self.CurrencyCode = data.get('CurrencyCode')

    def get_payment(self):
        return self.__dict__

class ListItem(object):
    def __init__(self, data):
        self.SKU = data.get('SKU')
        self.Description = data.get('Description')

    def get_list_item(self):
        return self.__dict__

class CreateAccessTokenRequest(object):
    def __init__(self):
        self.Customer = None
        self.ShippingAddress = None
        self.Payment = None
        self.Items = []
        self.Options = []
        self.RedirectUrl = ''
        self.Method = ''
        self.CustomerIP = ''
        self.DeviceID = ''

    def get_request(self):
        dict_data = self.__dict__
        if self.Customer:
            dict_data['Customer'] = self.Customer.get_customer()
        if self.ShippingAddress:
            dict_data['ShippingAddress'] = self.ShippingAddress.get_shipping_address()
        if self.Payment:
            dict_data['Payment'] = self.Payment.get_payment()
        return dict_data


#
# Copyright (c) 2020 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#

import json
import base64
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from common import consts
from utils.krauth import HTTPKrakenXBasicAuth, HTTPKrakenZBasicAuth

NO_AUTH = 0
BASIC_AUTH = 1
DIGEST_AUTH = 2
KRAKEN_AUTH = 3
KRAKEN_ZBASIC = 4


class RESTCommand(object):

    def __init__(self, module, command):
        self.module = module
        self.command = command

    def get(self, **kwargs):
        return self.module.get(self.command, **kwargs)

    def post(self, data=None, json_data=None, **kwargs):
        return self.module.post(self.command, data, json_data, **kwargs)

    def head(self, **kwargs):
        return self.module.head(self.command, **kwargs)

    def put(self, data=None, json_data=None, **kwargs):
        return self.module.put(self.command, data, json_data, **kwargs)

    @staticmethod
    def extract_message(message):
        msg_bytes = base64.b64decode(message)
        return json.loads(msg_bytes.decode("utf-8"))


class RESTModule(object):

    def __init__(self, service, module_name: str):
        self.service = service
        self.module_name = module_name

    def create_command(self, command):
        return RESTCommand(self, command)

    def get(self, command, **kwargs):
        return self.service.get(self.module_name, command, **kwargs)

    def post(self, command, data=None, json_data=None, **kwargs):
        return self.service.post(self.module_name, command, data, json_data, **kwargs)

    def head(self, command, **kwargs):
        return self.service.head(self.module_name, command, **kwargs)

    def put(self, command, data=None, json_data=None, **kwargs):
        return self.service.put(self.module_name, command, data, json_data, **kwargs)


class RESTService(object):

    def __init__(self, config=None, host_url=None, username=None, password=None, auth_type=None, parent=None):
        self.config = config
        self.host_url = host_url
        self.auth_type = BASIC_AUTH if auth_type is None else auth_type
        self.user = username
        self.passwd = password
        self.cookies = {}
        self.parent = parent
        if (self.host_url is None) and self.config and (consts.KRAKEN_REST_BASE_URL in self.config):
            self.host_url = self.config[consts.KRAKEN_REST_BASE_URL]
        if self.parent and not hasattr(self.parent, 'cookies'):
            setattr(self.parent, 'cookies', {})

    def set_user(self, username, password):
        self.user = username
        self.passwd = password

    def create_module(self, module):
        return RESTModule(self, module)

    def get_auth(self):
        if self.auth_type == BASIC_AUTH:
            return HTTPBasicAuth(self.user, self.passwd)
        elif self.auth_type == DIGEST_AUTH:
            return HTTPDigestAuth(self.user, self.passwd)
        elif self.auth_type == KRAKEN_AUTH:
            return HTTPKrakenXBasicAuth(self.user, self.passwd)
        elif self.auth_type == KRAKEN_ZBASIC:
            return HTTPKrakenZBasicAuth(self.user, self.passwd)
        return None

    def bind_url(self, module, command):
        return "{0}/{1}/{2}".format(self.host_url, module, command)

    def get(self, module, command, **kwargs):
        url = self.bind_url(module, command)
        cookies = self.cookies if not self.parent else self.parent.cookies
        resp = requests.get(url, params=kwargs, auth=self.get_auth(), cookies=cookies)
        cookies = resp.cookies.get('JSESSIONID')
        if cookies:
            if self.parent:
                if ('JSESSIONID' not in self.parent.cookies) or (self.parent.cookies['JSESSIONID'] != cookies):
                    self.parent.cookies['JSESSIONID'] = cookies
            else:
                self.cookies['JSESSIONID'] = cookies
        return resp

    def post(self, module, command, data=None, json_data=None, **kwargs):
        url = self.bind_url(module, command)
        cookies = self.cookies if not self.parent else self.parent.cookies
        resp = requests.post(url, data, json_data, params=kwargs, auth=self.get_auth(), cookies=cookies)
        cookies = resp.cookies.get('JSESSIONID')
        if cookies:
            if self.parent:
                if ('JSESSIONID' not in self.parent.cookies) or (self.parent.cookies['JSESSIONID'] != cookies):
                    self.parent.cookies['JSESSIONID'] = cookies
            else:
                self.cookies['JSESSIONID'] = cookies
        return resp

    def head(self, module, command, **kwargs):
        url = self.bind_url(module, command)
        cookies = self.cookies if not self.parent else self.parent.cookies
        resp = requests.head(url, **kwargs, auth=self.get_auth(), cookies=cookies)
        cookies = resp.cookies.get('JSESSIONID')
        if cookies:
            if self.parent:
                if ('JSESSIONID' not in self.parent.cookies) or (self.parent.cookies['JSESSIONID'] != cookies):
                    self.parent.cookies['JSESSIONID'] = cookies
            else:
                self.cookies['JSESSIONID'] = cookies
        return resp

    def put(self, module, command, data=None, json_data=None, **kwargs):
        url = self.bind_url(module, command)
        cookies = self.cookies if not self.parent else self.parent.cookies
        resp = requests.put(url, data, json_data, **kwargs, auth=self.get_auth(), cookies=cookies)
        cookies = resp.cookies.get('JSESSIONID')
        if cookies:
            if self.parent:
                if ('JSESSIONID' not in self.parent.cookies) or (self.parent.cookies['JSESSIONID'] != cookies):
                    self.parent.cookies['JSESSIONID'] = cookies
            else:
                self.cookies['JSESSIONID'] = cookies
        return resp
    
    def get_cookies(self):
        return self.cookies
    
    def set_cookies(self, cookies):
        self.cookies = cookies




#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from utils.krauth import HTTPKrakenXBasicAuth, HTTPKrakenZBasicAuth
from requests_jwt import JWTAuth


NO_AUTH = 0
BASIC_AUTH = 1
DIGEST_AUTH = 2
KRAKEN_AUTH = 3
KRAKEN_ZBASIC = 4
JWT_AUTH = 5


class BaseHttpClient(object):

    def __init__(self, config=None, host_url=None, username=None, password=None, secret_token=None,
                 auth_type=None, parent=None):
        self._config = config
        self._host_url = host_url
        self._auth_type = NO_AUTH if auth_type is None else auth_type
        self._user = username
        self._passwd = password
        self._cookies = {}
        self._parent = parent
        self._token = secret_token
        if self._parent and not hasattr(self._parent, "cookies"):
            self._parent.cookies = dict()

    def set_user(self, username, password):
        self._user = username
        self._passwd = password

    def set_token(self, secret_token):
        self._token = secret_token

    def get_token(self):
        return self._token

    def get_auth(self):
        if self._auth_type == BASIC_AUTH:
            return HTTPBasicAuth(self._user, self._passwd)
        elif self._auth_type == DIGEST_AUTH:
            return HTTPDigestAuth(self._user, self._passwd)
        elif self._auth_type == KRAKEN_AUTH:
            return HTTPKrakenXBasicAuth(self._user, self._passwd)
        elif self._auth_type == KRAKEN_ZBASIC:
            return HTTPKrakenZBasicAuth(self._user, self._passwd)
        elif self._auth_type == JWT_AUTH:
            return JWTAuth(self._token)
        return None

    def _bind_url(self, resource):
        return "{0}/{1}".format(self._host_url, resource)

    def update_cookies(self, resp):
        cookies = self._parent.cookies if self._parent else self._cookies
        cookies.update([(name, value) for name, value in resp.cookies.iteritems()])

    def get(self, resource, **kwargs):
        url = self._bind_url(resource)
        cookies = self._parent.cookies if self._parent else self._cookies
        resp = requests.get(url, params=kwargs, auth=self.get_auth(), cookies=cookies)
        self.update_cookies(resp)
        return resp

    def post(self, resource, data=None, json_data=None, **kwargs):
        url = self._bind_url(resource)
        cookies = self._parent.cookies if self._parent else self._cookies
        resp = requests.post(url, data, json_data, params=kwargs, auth=self.get_auth(), cookies=cookies)
        self.update_cookies(resp)
        return resp

    def head(self, resource, **kwargs):
        url = self._bind_url(resource)
        cookies = self._parent.cookies if self._parent else self._cookies
        resp = requests.head(url, **kwargs, auth=self.get_auth(), cookies=cookies)
        self.update_cookies(resp)
        return resp

    def put(self, resource, data=None, json_data=None, **kwargs):
        url = self._bind_url(resource)
        cookies = self._parent.cookies if self._parent else self._cookies
        resp = requests.put(url, data, json_data, **kwargs, auth=self.get_auth(), cookies=cookies)
        self.update_cookies(resp)
        return resp

    def get_parent(self):
        return self._parent

    def get_cookies(self):
        return self._cookies

    def set_cookies(self, cookies):
        self._cookies = cookies

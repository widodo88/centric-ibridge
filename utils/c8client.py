#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#
# This module is part of Centric PLM Integration Bridge and is released under
# the Apache-2.0 License: https://www.apache.org/licenses/LICENSE-2.0


import json
import base64
import time
from common import consts
from utils.basehttpclient import BaseHttpClient, JWT_AUTH

C8_TOKEN_NAME = "SecurityTokenURL"


class C8WebResource(object):
    def __init__(self, service, resource: str):
        self._service = service
        self._resource = resource

    def get(self, **kwargs):
        return self._service.do_get(self._resource, **kwargs)

    def post(self, data=None, json_data=None, **kwargs):
        return self._service.do_post(self._resource, data, json_data, **kwargs)

    def head(self, **kwargs):
        return self._service.do_head(self._resource, **kwargs)

    def put(self, data=None, json_data=None, **kwargs):
        return self._service.do_put(self._resource, data, json_data, **kwargs)

    @staticmethod
    def extract_message(message):
        msg_bytes = base64.b64decode(message)
        return json.loads(msg_bytes.decode("utf-8"))


class C8WebClient(BaseHttpClient):

    def __init__(self, config=None, host_url=None, secret_token=None, auth_type=None, parent=None):
        auth_type = JWT_AUTH if auth_type is None else auth_type
        if (host_url is None) and config and (consts.C8_REST_BASE_URL in config):
            host_url = config[consts.C8_REST_BASE_URL]
        if parent and not hasattr(parent, 'cookies'):
            setattr(parent, 'cookies', {})
        super(C8WebClient, self).__init__(config=config, host_url=host_url, secret_token=secret_token,
                                          auth_type=auth_type, parent=parent)

    def create_resource(self, resource):
        return C8WebResource(self, resource)

    def update_cookies(self, resp):
        super(C8WebClient, self).update_cookies(resp)
        token = self.get_token()
        cookies = self.get_parent()
        cookies = cookies.cookies if cookies else cookies
        cookies = cookies if cookies else self.get_cookies()
        token = cookies[C8_TOKEN_NAME] if C8_TOKEN_NAME in cookies else token
        self.set_token(token)

    def update_login_info(self, resp):
        parent = self.get_parent()
        if not parent:
            return
        parent.last_c8login = time.time()
        self.update_cookies(resp)

    def login_expired(self):
        parent = self.get_parent()
        if not parent or not hasattr(parent, "last_c8login"):
            return True
        # ensure last login < 30 minutes
        elapsed_time = time.time() - parent.last_c8login
        return elapsed_time > 1800

    def do_get(self, resource, **kwargs):
        return self.get(resource, **kwargs)

    def do_post(self, resource, data=None, json_data=None, **kwargs):
        return self.post(resource, data=data, json_data=json_data, **kwargs)

    def do_head(self, resource, **kwargs):
        return self.head(resource, **kwargs)

    def do_put(self, resource, data=None, json_data=None, **kwargs):
        return self.post(resource, data=data, json_data=json_data, **kwargs)

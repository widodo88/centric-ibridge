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

from typing import Type
import json
import base64
from utils.basehttpclient import BaseHttpClient


class HttpWebResource(object):
    def __init__(self):
        self._service = None
        self._resource = None

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

    def prepare_resource(self, service: object, resource: str):
        self._service = service
        self._resource = resource


class HttpClient(BaseHttpClient):

    def __init__(self, config: dict = None, host_url: str = None, username=None, password=None, secret_token=None,
                 auth_type=None, parent: object = None, klass: Type[object] = HttpWebResource):
        super(HttpClient, self).__init__(config=config, host_url=host_url, username=username, password=password,
                                         secret_token=secret_token, auth_type=auth_type, parent=parent)
        self._klass = klass

    def create_resource(self, resource):
        instance = object.__new__(self._klass)
        instance.__init__()
        if isinstance(instance, HttpWebResource):
            instance.prepare_resource(self, resource)
        return instance

    def do_get(self, resource, **kwargs):
        return self.get(resource, **kwargs)

    def do_post(self, resource, data=None, json_data=None, **kwargs):
        return self.post(resource, data=data, json_data=json_data, **kwargs)

    def do_head(self, resource, **kwargs):
        return self.head(resource, **kwargs)

    def do_put(self, resource, data=None, json_data=None, **kwargs):
        return self.post(resource, data=data, json_data=json_data, **kwargs)

    @staticmethod
    def extract_message(message):
        msg_bytes = base64.b64decode(message)
        return json.loads(msg_bytes.decode("utf-8"))

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
from common import consts
from utils.absrest import AbstractRestService, JWT_AUTH


class C8RESTResource(object):
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


class C8RESTService(AbstractRestService):

    def __init__(self, config=None, host_url=None, secret_token=None, auth_type=None, parent=None):
        auth_type = JWT_AUTH if auth_type is None else auth_type
        if (host_url is None) and config and (consts.C8_REST_BASE_URL in config):
            host_url = config[consts.C8_REST_BASE_URL]
        if parent and not hasattr(parent, 'cookies'):
            setattr(parent, 'cookies', {})
        super(C8RESTService, self).__init__(config=config, host_url=host_url, secret_token=secret_token,
                                            auth_type=auth_type, parent=parent)

    def create_resource(self, resource):
        return C8RESTResource(self, resource)

    @staticmethod
    def _resource_url(module, command):
        return "{0}/{1}".format(module, command)

    def do_get(self, module, command, **kwargs):
        resource = self._resource_url(module, command)
        return self.get(resource, **kwargs)

    def do_post(self, module, command, data=None, json_data=None, **kwargs):
        resource = self._resource_url(module, command)
        return self.post(resource, data=data, json_data=json_data, **kwargs)

    def do_head(self, module, command, **kwargs):
        resource = self._resource_url(module, command)
        return self.head(resource, **kwargs)

    def do_put(self, module, command, data=None, json_data=None, **kwargs):
        resource = self._resource_url(module, command)
        return self.post(resource, data=data, json_data=json_data, **kwargs)

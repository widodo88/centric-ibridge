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

import json
import base64
from common import consts
from utils.absrest import AbstractRestService, KRAKEN_ZBASIC


class RESTCommand(object):

    def __init__(self, module, command):
        self._module = module
        self._command = command

    def get(self, **kwargs):
        return self._module.get(self._command, **kwargs)

    def post(self, data=None, json_data=None, **kwargs):
        return self._module.post(self._command, data, json_data, **kwargs)

    def head(self, **kwargs):
        return self._module.head(self._command, **kwargs)

    def put(self, data=None, json_data=None, **kwargs):
        return self._module.put(self._command, data, json_data, **kwargs)

    @staticmethod
    def extract_message(message):
        msg_bytes = base64.b64decode(message)
        return json.loads(msg_bytes.decode("utf-8"))


class RESTModule(object):

    def __init__(self, service, module_name: str):
        self._service = service
        self._module_name = module_name

    def create_command(self, command):
        return RESTCommand(self, command)

    def get(self, command, **kwargs):
        return self._service.do_get(self._module_name, command, **kwargs)

    def post(self, command, data=None, json_data=None, **kwargs):
        return self._service.do_post(self._module_name, command, data, json_data, **kwargs)

    def head(self, command, **kwargs):
        return self._service.do_head(self._module_name, command, **kwargs)

    def put(self, command, data=None, json_data=None, **kwargs):
        return self._service.do_put(self._module_name, command, data, json_data, **kwargs)


class KRESTService(AbstractRestService):

    def __init__(self, config=None, host_url=None, username=None, password=None, auth_type=None, parent=None):
        auth_type = KRAKEN_ZBASIC if auth_type is None else auth_type
        if (host_url is None) and config and (consts.KRAKEN_REST_BASE_URL in config):
            host_url = config[consts.KRAKEN_REST_BASE_URL]
        if parent and not hasattr(parent, 'cookies'):
            setattr(parent, 'cookies', {})
        super(KRESTService, self).__init__(config=config, host_url=host_url, username=username, password=password,
                                           auth_type=auth_type, parent=parent)

    def create_module(self, module):
        return RESTModule(self, module)

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

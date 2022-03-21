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
import typing as t
from common import msgobject as mo
from core.transhandler import TransportHandler


class BaseProxy(object):

    def __init__(self):
        super(BaseProxy, self).__init__()
        self.transport: t.Optional[TransportHandler] = None

    def set_transport_adapter(self, transport: TransportHandler):
        self.transport = transport

    def __getattr__(self, item):
        return MethodProxy(self, item)

    def set_remote_method(self, method):
        ...


class MethodProxy(object):

    def __init__(self, message_obj: BaseProxy, method: str):
        self.message_object = message_obj
        self.message_object.set_remote_method(method)

    def __call__(self, *args, **kwargs):
        transport = self.message_object.transport
        self.message_object.set_parameters(*args, **kwargs)
        transport.notify_server(self.message_object)


class MessageCommandProxy(mo.MessageCommand, BaseProxy):

    def __init__(self, module: str, submodule: str, transport: TransportHandler):
        super(MessageCommandProxy, self).__init__()
        self.set_message(module, submodule, None)
        self.set_transport_adapter(transport)

    def set_remote_method(self, method):
        self.COMMAND = method


class MessageEventProxy(mo.MessageEvent, BaseProxy):

    def __init__(self, module: str, submodule: str, transport: TransportHandler):
        super(MessageEventProxy, self).__init__()
        self.set_message(module, submodule, None)
        self.set_transport_adapter(transport)

    def set_remote_method(self, method):
        self.EVENT = method


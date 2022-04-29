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

from common import consts
from common.startable import LifeCycleManager
from core.transhandler import TransportMessageNotifier


class BaseAppServer(LifeCycleManager):

    def __init__(self, config=None, standalone=False):
        super(BaseAppServer, self).__init__(config=config)
        self._transport_listener = None
        self._production_mode = None
        self._standalone = standalone
        self._async_mode = None

    def do_configure(self):
        self._lazy_configure() if self._production_mode is None else None
        super(BaseAppServer, self).do_configure()

    def handle_stop_event(self, obj):
        pass

    def configure_transport(self):
        transport_listener = self.get_transport_listener()
        transport_listener = transport_listener if transport_listener else self.create_transport_listener()
        return transport_listener

    def get_transport_listener(self):
        return self._transport_listener

    def set_transport_listener(self, listener):
        self._transport_listener = listener

    def create_transport_listener(self):
        return TransportMessageNotifier(stopped_func=self.handle_stop_event)

    def is_standalone(self):
        return self._standalone

    @property
    def standalone(self):
        return self._standalone

    @standalone.setter
    def standalone(self, value):
        self._standalone = value

    def is_production_mode(self):
        self._lazy_configure() if self._production_mode is None else None
        return self._production_mode

    def is_async_mode(self):
        self._lazy_configure() if self._async_mode is None else None
        return self._async_mode

    def _lazy_configure(self):
        config = self.get_configuration()
        mode = "false" if consts.PRODUCTION_MODE not in config else config[consts.PRODUCTION_MODE]
        mode = "false" if mode is None else mode
        self._production_mode = mode.lower() == "true"
        mode = "false" if consts.USE_ASYNC not in config else config[consts.USE_ASYNC]
        mode = "false" if mode is None else mode
        self._async_mode = mode.lower() == "true"


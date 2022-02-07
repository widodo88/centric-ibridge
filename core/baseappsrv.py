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

from core.startable import LifeCycleManager
from core.transhandler import TransportMessageNotifier


class BaseAppServer(LifeCycleManager):

    def __init__(self, config=None, standalone=False):
        super(BaseAppServer, self).__init__(config=config)
        self._transport_listener = None
        self._standalone = standalone

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

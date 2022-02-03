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

import logging
from core.startable import LifeCycleManager
from core.transhandler import TransportMessageNotify
from core.shutdn import ShutdownHookMonitor
from core.transport.xsocktransport import UnixSocketTransport
from core.transport.localtransport import LocalhostTransport
from core.transfactory import TransportPreparer
from utils import oshelper


class BridgeServer(LifeCycleManager):

    def configure_transport(self, listener):
        config = self.get_configuration()
        TransportPreparer.prepare_transports(config, listener, self)

    def do_configure(self):
        cfg = self.get_configuration()
        default_listener = TransportMessageNotify(message_func=self.on_message_recv,
                                                  stopped_func=self.on_terminate_signal)
        shutdown_hook = ShutdownHookMonitor.get_default_instance()
        shutdown_hook.set_configuration(cfg)
        shutdown_hook.add_listener(default_listener)
        self.add_object(shutdown_hook)
        local_transport = UnixSocketTransport(cfg) if not oshelper.is_windows() else LocalhostTransport(cfg)
        local_transport.add_listener(default_listener)
        self.add_object(local_transport)
        super(BridgeServer, self).do_configure()

    def on_message_recv(self, obj, message):
        logging.info(message)

    def on_terminate_signal(self, obj):
        self.stop()
        logging.info("Shutting down")

    def send_shutdown_signal(self):
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        if shutdown_monitor:
            shutdown_monitor.send_shutdown_signal()

    def join(self):
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        if shutdown_monitor:
            shutdown_monitor.join()

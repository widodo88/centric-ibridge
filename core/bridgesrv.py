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
from core.transhandler import TransportMessageNotifier
from core.shutdn import ShutdownHookMonitor
from core.transfactory import TransportPreparer
from core.msghandler import QueuePoolHandler, MessageNotifier
from core. msgexec import MessageExecutionManager
from utils import oshelper, transhelper


class BridgeServer(LifeCycleManager):

    def configure_transport(self):
        config = self.get_configuration()
        transport_listener = TransportMessageNotifier(stopped_func=self.on_terminate_signal)
        TransportPreparer.prepare_transports(config, transport_listener, self)
        return transport_listener

    def do_configure(self):
        cfg = self.get_configuration()
        transport_listener = self.configure_transport()

        local_transport = transhelper.get_local_transport()
        local_transport.set_configuration(cfg)
        local_transport.add_listener(transport_listener)
        self.add_object(local_transport)

        message_listener = MessageNotifier()
        execution_manager = MessageExecutionManager(cfg)
        execution_manager.register_listener(message_listener)
        self.add_object(execution_manager)

        message_pool = QueuePoolHandler()
        message_pool.register_listener(transport_listener)
        message_pool.add_listener(message_listener)
        self.add_object(message_pool)

        shutdown_hook = ShutdownHookMonitor.get_default_instance()
        shutdown_hook.set_configuration(cfg)
        shutdown_hook.add_listener(transport_listener)
        self.add_object(shutdown_hook)

        super(BridgeServer, self).do_configure()

    def on_terminate_signal(self, obj):
        self.stop()
        logging.info("Shutting down")

    def send_shutdown_signal(self):
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        shutdown_monitor.send_shutdown_signal() if shutdown_monitor else None

    def notify_server(self, message_obj):
        config = self.get_configuration()
        local_transport = transhelper.get_local_transport()
        local_transport.set_configuration(config)
        local_transport.notify_server(message_obj)

    def alt_shutdown_signal(self):
        config = self.get_configuration()
        local_transport = transhelper.get_local_transport()
        local_transport.set_configuration(config)
        local_transport.send_shutdown_signal()

    def join(self):
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        shutdown_monitor.join() if shutdown_monitor else None

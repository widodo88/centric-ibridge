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
from core.startable import LifeCycleManager, StartableListener
from core.shutdn import ShutdownHookMonitor


class BridgeServer(LifeCycleManager):

    def do_configure(self):
        shutdown_hook = ShutdownHookMonitor.get_default_instance()
        shutdown_hook.add_listener(StartableListener(stopped_func=self.on_terminate_signal))
        self.add_object(shutdown_hook)
        super(BridgeServer, self).do_configure()

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







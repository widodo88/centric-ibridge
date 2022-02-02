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

from threading import Thread, RLock
from socket import AF_INET, socket, SOCK_STREAM
from core.startable import Startable
from common import consts
import logging


class ShutdownHookMonitor(Startable):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None):
        super(ShutdownHookMonitor, self).__init__(config)
        self.socket = None
        self.shutdown_thread = None
        self.shutdown_addr = None
        self.shutdown_port = None

    def send_shutdown_signal(self):
        config = self.get_configuration()
        self.shutdown_addr = config[consts.SHUTDOWN_ADDR] if config and consts.SHUTDOWN_ADDR in config else consts.DEFAULT_SHUTDOWN_ADDR
        self.shutdown_port = config[consts.SHUTDOWN_PORT] if config and consts.SHUTDOWN_PORT in config else consts.DEFAULT_SHUTDOWN_PORT
        self.shutdown_port = int(self.shutdown_port) if isinstance(self.shutdown_port, str) else self.shutdown_port
        client = socket(AF_INET, SOCK_STREAM)
        client.connect((self.shutdown_addr, self.shutdown_port))
        fd = client.makefile(mode="w")
        fd.write("shut\n")
        fd.flush()
        fd.close()
        client.close()

    def join(self, timeout=None):
        if not self.is_running():
            raise Exception("Shutdown Listener is not Running")
        self.shutdown_thread.join(timeout)

    def do_configure(self):
        config = self.get_configuration()
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.shutdown_addr = config[consts.SHUTDOWN_ADDR] if config and consts.SHUTDOWN_ADDR in config else consts.DEFAULT_SHUTDOWN_ADDR
        self.shutdown_port = config[consts.SHUTDOWN_PORT] if config and consts.SHUTDOWN_PORT in config else consts.DEFAULT_SHUTDOWN_PORT
        self.shutdown_port = int(self.shutdown_port) if isinstance(self.shutdown_port, str) else self.shutdown_port
        self.shutdown_thread = Thread(target=self.listen, daemon=True, name="StopMonitor")

    def do_start(self):
        self.socket.bind((self.shutdown_addr, self.shutdown_port))
        self.socket.listen(1)
        self.shutdown_thread.start()

    def do_stop(self):
        self.socket.close()

    def listen(self):
        client = None
        should_terminate = False
        while self.is_running():
            try:
                if not should_terminate:
                    client, client_addr = self.socket.accept()
                    fp = client.makefile('r', buffering=512)
                    info = fp.readline()
                    should_terminate = isinstance(info, str) and (info.strip().lower() == 'shut')
                    fp.close()
            except Exception as ex:
                logging.error(ex)
            finally:
                try:
                    if client:
                        client.close()
                    if should_terminate:
                        self.stop()
                except:
                    pass
                finally:
                    client = None

    @classmethod
    def get_default_instance(cls):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()
            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()




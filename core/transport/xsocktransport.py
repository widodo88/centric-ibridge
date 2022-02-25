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

import logging
import time
import socket
import selectors
import os
import os.path
from common import consts
from core.transport.localtransport import LocalhostTransport


class UnixSocketTransport(LocalhostTransport):

    def do_configure(self):
        super(UnixSocketTransport, self).do_configure()
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()

    def prepare_listening(self):
        if os.path.exists(consts.UNIX_SOCKET_FILE):
            os.remove(consts.UNIX_SOCKET_FILE)
        self.socket.bind(consts.UNIX_SOCKET_FILE)
        self.socket.setblocking(False)
        self.socket.listen()
        self.selector.register(self.socket, selectors.EVENT_READ)

    def publish_message(self, message_obj):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(consts.UNIX_SOCKET_FILE)
        try:
            fd = client.makefile(mode="w")
            try:
                fd.write("{0}\n".format(message_obj.encode().decode("utf-8")))
                fd.flush()
            finally:
                fd.close()
        finally:
            client.close()

    def send_shutdown_signal(self):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(consts.UNIX_SOCKET_FILE)
        try:
            fd = client.makefile(mode="w")
            try:
                fd.write("shut\n")
                fd.flush()
            finally:
                fd.close()
        finally:
            client.close()




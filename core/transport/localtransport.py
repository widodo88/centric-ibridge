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
import socket
from common import consts
from core.transhandler import TransportHandler


class LocalhostTransport(TransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(LocalhostTransport, self).__init__(config, transport_index)
        self.socket = None

    def do_configure(self):
        super(LocalhostTransport, self).do_configure()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def do_listen(self):
        client = None
        should_terminate = False
        self.socket.bind((consts.LOCAL_TRANSPORT_ADDR, consts.LOCAL_TRANSPORT_PORT))
        self.socket.listen(1)
        while self.is_running():
            try:
                if not should_terminate:
                    client, client_addr = self.socket.accept()
                    fp = client.makefile('r', buffering=1024)
                    message = fp.readline()
                    fp.close()
                    should_terminate = isinstance(message, str) and (message.strip().lower() == 'shut')
                    if not should_terminate:
                        self.handle_message(message)
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


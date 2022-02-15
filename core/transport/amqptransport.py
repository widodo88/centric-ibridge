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

import amqp
import logging
from common import consts
from core.transhandler import TransportHandler
import time


class AmqpTransport(TransportHandler):
    def __init__(self, config=None, transport_index=0):
        super(AmqpTransport, self).__init__(config=config, transport_index=transport_index)
        self.amqp_config = None
        self.host = None
        self.client = None

    def do_configure(self):
        super(AmqpTransport, self).do_configure()
        self.host = "{0}:{1}".format(self.get_transport_address(), self.get_transport_port())

    def doConnect(self):
        with amqp.Connection(host=self.host, userid=self.get_transport_user(),
                             password=self.get_transport_password()) as self.amqp_config:
            self.client = self.amqp_config.channel()
            self.client.basic_consume(queue=self.get_transport_channel(), callback=self.handle_message)

    def do_listen(self):
        try:
            try:
                while self.is_running():
                    self.doConnect()
                self.client.close()
            except Exception as ex:
                logging.error(ex)
                self.client.close()
                raise
        finally:
            self.amqp_config.close()

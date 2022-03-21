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

import time
import traceback
import logging
from kafka import KafkaConsumer, KafkaProducer
from common.msgobject import AbstractMessage
from core.transhandler import TransportHandler


class KafkaTransport(TransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(KafkaTransport, self).__init__(config=config, transport_index=transport_index)
        self._kafka_topic = None
        self._kafka_group_id = None
        self._connection = None

    def do_configure(self):
        super(KafkaTransport, self).do_configure()
        kafka_topic = self._transport_channel.split(",") if isinstance(self._transport_channel, str) else [""]
        self._kafka_group_id = kafka_topic[1] if len(kafka_topic) > 1 else None
        self._kafka_topic = kafka_topic[0].split(",")
        address = "{}:{}".format(self.get_transport_address(), self.get_transport_port())
        self._connection = KafkaConsumer(*self._kafka_topic, group_id=self._kafka_group_id, bootstrap_servers=address,
                                         sasl_plain_username=self.get_transport_user(),
                                         sasl_plain_password=self.get_transport_password(),
                                         sasl_mechanism='PLAIN')

    def do_listen(self):
        logging.info("Subscribing {} on topic {}".format(self.get_transport_address(), self._kafka_topic))
        self._connection.subscribe(self._kafka_topic)
        try:
            try:
                while self.is_running():
                    output: dict = self._connection.poll()
                    for key in output:
                        for message in output[key]:
                            self.handle_message(message)
                    if not output:
                        time.sleep(0.2)
            finally:
                self._connection.unsubscribe()
        finally:
            self._connection.close(True)

    def publish_message(self, message_obj: AbstractMessage):
        address = "{}:{}".format(self.get_transport_address(), self.get_transport_port())
        kafka_topic = self._transport_channel.split(",") if isinstance(self._transport_channel, str) else [""]
        publisher = KafkaProducer(bootstrap_servers=address)
        publisher.send(kafka_topic[0], message_obj.encode())


        

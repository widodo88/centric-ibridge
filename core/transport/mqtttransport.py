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

from paho.mqtt import client as mqtt
from common import consts
from core.transhandler import TransportHandler
import logging


class MqttTransport(TransportHandler):

    client = None

    def __init__(self):
        self.client = None
        self.client_id = None
        super(MqttTransport, self).__init__()

    def do_configure(self):
        self.client_id = self._get_config_value(consts.MQ_TRANSPORT_CLIENT_ID, 'ecfbridge01')
        super(MqttTransport, self).do_configure()

    def on_message(self, obj, msg):
        if msg:
            self.handle_message(msg)

    def on_subscribe(self, client, obj, mid, granted_qos):
        pass

    @staticmethod
    def on_connect(client, obj, flags, rc):
        logging.info("Connected to mqtt broker")

    def do_listen(self):
        self.client = mqtt.Client(self.client_id)
        logging.info("Subscribing {} on {}".format(self.get_transport_address(), self.get_transport_channel()))
        self.client.on_connect = self.on_connect
        self.client.on_connect = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.connect(self.get_transport_address(), self.get_transport_port())
        self.client.subscribe(self.get_transport_channel())
        self.client.loop_forever()

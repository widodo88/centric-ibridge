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
from uuid import uuid4

from paho.mqtt import client as mqtt

from core.transhandler import TransportHandler


class MqttTransport(TransportHandler):
    client = None

    def __init__(self):
        self.client = None
        self.client_id = str(uuid4())
        self.subscribed = False
        super(MqttTransport, self).__init__()

    def do_configure(self):
        super(MqttTransport, self).do_configure()

    def on_message(self, client, usrdata, msg):
        if msg:
            self.handle_message(msg.payload.decode())

    def on_subscribe(self, client, obj, mid, granted_qos):
        self.subscribed = 1

    def on_disconnect(self, client, userdata, rc):
        logging.info("Disconnected to mqtt broker")
        self.subscribed = 0

    def on_connect(self, client, obj, flags, rc):
        logging.info("Connected to mqtt broker")
        if not self.subscribed:
            self.client.subscribe(self.get_transport_channel())

    def do_listen(self):
        self.client = mqtt.Client(self.client_id)
        logging.info("Subscribing {} on {}".format(self.get_transport_address(), self.get_transport_channel()))
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_disconnect = self.on_disconnect
        self.client.connect(self.get_transport_address(), self.get_transport_port())
        self.client.subscribe(self.get_transport_channel())
        self.client.loop_forever()

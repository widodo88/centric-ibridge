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
import threading
import time
from common import consts
from core.startable import Startable, StartableListener


class TransportMessageNotify(StartableListener):

    def __init__(self, message_func=None):
        super(TransportMessageNotify, self).__init__()
        self._message = message_func

    def on_message_received(self, obj, msg):
        if self._message:
            self._message(obj, msg)


class TransportHandler(Startable):

    def __init__(self, config=None, transport_index=0):
        super(TransportHandler, self).__init__(config)
        self._transport_thread = threading.Thread(target=self.listen)
        self._transport_index = transport_index
        self._target_address = None
        self._target_port = None
        self._target_username = None
        self._target_password = None
        self._target_channel = None

    def do_listen(self):
        pass

    def do_configure(self):
        super(TransportHandler).do_configure()
        self._target_address = self._get_config_value(consts.MQ_TRANSPORT_ADDR, "127.0.0.1")
        self._target_port = self._get_config_value(consts.MQ_TRANSPORT_PORT, None)
        self._target_username = self._get_config_value(consts.MQ_TRANSPORT_USER, None)
        self._target_password = self._get_config_value(consts.MQ_TRANSPORT_PASS, None)
        self._target_channel = self._get_config_value(consts.MQ_TRANSPORT_CHANNEL, None)

    def do_start(self):
        super(TransportHandler, self).do_start()
        if self.is_enabled():
            self._transport_thread.start()

    def handle_message(self, message):
        valid_listeners = [listener for listener in self.get_listeners() if
                           isinstance(listener, TransportMessageNotify)]
        for listener in valid_listeners:
            listener.on_message_received(self, message)

    def listen(self):
        while self.is_running():
            try:
                self.do_listen()
            except Exception as ex:
                logging.error(ex)
                if self.is_running():
                    time.sleep(5)

    def get_transport_index(self):
        return self._transport_index

    def get_transport_address(self):
        return self._target_address

    def get_transport_port(self):
        return self._target_port

    def get_transport_user(self):
        return self._target_username

    def get_transport_password(self):
        return self._target_password

    def get_transport_channel(self):
        return self._target_channel

    def _get_config_value(self, key, def_value):
        config = self.get_configuration()
        config_key = str(key).format(self._transport_index)
        return def_value if config_key not in config else config[config_key]


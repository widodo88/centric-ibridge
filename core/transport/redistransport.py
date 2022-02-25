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
import logging
from redis import Redis
from core.transhandler import TransportHandler
from core.redisprovider import RedisProvider
from typing import Union


class RedisTransport(TransportHandler):

    def __init__(self, config=None, transport_index=0):
        super(RedisTransport, self).__init__(config=config, transport_index=transport_index)
        self._client: Union[Redis, None] = None

    def do_configure(self):
        super(RedisTransport, self).do_configure()
        self._get_provider()

    def do_listen(self):
        self.connect()
        try:
            pubsub = self._client.pubsub()
            pubsub.subscribe(self.get_transport_channel())
            try:
                while self.is_running() and pubsub.subscribed:
                    response = pubsub.handle_message(pubsub.parse_response(block=False, timeout=1))
                    if response and isinstance(response, dict):
                        self.handle_message(response.get('data'))
                    else:
                        time.sleep(0.4)
            except Exception as ex:
                logging.exception(ex)
            finally:
                pubsub.unsubscribe(self.get_transport_channel())
                pubsub.reset()
        finally:
            self.disconnect()

    def connect(self):
        provider = self._get_provider()
        self._client = Redis(connection_pool=provider.get_pool())

    def disconnect(self):
        self._client.close() if self._client else None

    def publish_message(self, message_obj):
        self._client.publish(self.get_transport_channel(), message_obj.encode().decode("utf-8"))

    @staticmethod
    def _get_provider():
        provider = RedisProvider.get_default_instance()
        assert provider.is_enabled(), "Redis must be enabled to use this transport"
        return provider


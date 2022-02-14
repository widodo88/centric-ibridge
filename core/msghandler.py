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

import queue
import time
import threading
from core.startable import Startable, StartableListener


class MessageNotifier(StartableListener):

    def __init__(self, message_func=None, starting_func=None, started_func=None, failure_func=None,
                 stopping_func=None, stopped_func=None, configuring_func=None, configured_func=None):
        super(MessageNotifier, self).__init__(starting_func, started_func, failure_func, stopping_func,
                                              stopped_func, configuring_func, configured_func)
        self._message = message_func

    def on_message_received(self, obj, msg):
        if (not msg) or (not self._message):
            return
        self._message(obj, msg)

    def set_on_message_received(self, message_func=None):
        self._message = message_func

    def get_on_message_received(self):
        return self._message


class MessageHandler(Startable):

    def handle_message(self, message):
        if message in [None, '']:
            return
        valid_listeners = [listener for listener in self.get_listeners() if
                           isinstance(listener, MessageNotifier)]
        for listener in valid_listeners:
            listener.on_message_received(self, message)


class QueuePoolHandler(MessageHandler):

    def __init__(self):
        super(QueuePoolHandler, self).__init__()
        self._handler = None
        self._queue = queue.Queue()
        self._eval_thread = threading.Thread(target=self._eval_message, daemon=True)

    def register_listener(self, listener):
        listener.set_on_message_received(self.on_handle_message) if isinstance(listener, MessageNotifier) else None

    def on_handle_message(self, obj, message):
        self._queue.put(message, block=True)

    def do_start(self):
        self._eval_thread.start()

    def do_stop(self):
        with self._queue.mutex:
            self._queue.queue.clear()

    def _eval_message(self):
        while self.is_running():
            if self._queue.empty():
                time.sleep(1)
            else:
                message = self._queue.get(block=True)
                self.handle_message(message)

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

from core.msghandler import MessageHandler, MessageReceiver


class TransportAdapter(MessageHandler, MessageReceiver):
    
    def __init__(self, config=None):
        super(TransportAdapter, self).__init__(config=config)

    def transform_message(self, obj: object, message: str) -> str:
        raise NotImplementedError

    def validate_message(self, obj: object, message: str):
        return obj and (message is not None)

    def process_message(self, obj: object, message: str):
        transformed_msg = self.transform_message(obj, message)
        self.handle_message(transformed_msg)

    def on_message_received(self, obj: object, message: str):
        if not self.validate_message(obj, message):
            return
        self.process_message(obj, message)


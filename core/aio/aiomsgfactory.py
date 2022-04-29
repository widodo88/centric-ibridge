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
from core.msgpexec import ShutdownMessage
from core.msgfactory import MessageFactory
from common.msgobject import AbstractMessage


class AsyncMessageFactory(MessageFactory):

    @classmethod
    def generate(cls, message):
        msg_data = message.encode("utf-8") if isinstance(message, str) else message
        obj = super(AsyncMessageFactory, cls).generate(msg_data)
        if not obj:
            cmd_dict = cls.extract_message(message) \
                if isinstance(message, bytes) else message if isinstance(message, dict) else None
            klass = ShutdownMessage if cmd_dict and ('msgtype' in cmd_dict) and (cmd_dict['msgtype'] == 999) else None
            obj = cls.__create_instance__(klass) if klass else None
            obj.setup(cmd_dict) if obj and isinstance(obj, AbstractMessage) else None
        return obj


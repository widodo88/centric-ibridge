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

import uuid
try:
    import pybase64 as base64
except:
    import base64

try:
    import ujson as json
except:
    import json

MODE_COMMAND = 0
MODE_EVENT = 1


def mq_command(f):
    f.mq_type = MODE_COMMAND
    return f


def mq_event(f):
    f.mq_type = MODE_EVENT
    return f


def get_module_id(mod, submod):
    return "{0}@{1}".format(mod, submod)


class Extractable(object):

    @staticmethod
    def extract_message(message: bytes):
        return json.loads(message.decode("utf-8"))


class BaseMessage(Extractable):

    def __init__(self, msg_type=None):
        super(BaseMessage, self).__init__()
        self.message_mode = msg_type


class AbstractMessage(BaseMessage):

    def __init__(self, message=None, msg_type=None):
        super(AbstractMessage, self).__init__(msg_type=msg_type)
        self.MESSAGE_ID = None
        self.MODULE = None
        self.SUBMODULE = None
        self.PARAMS = None
        self.message_options = dict()
        self.process_message(message)

    def process_message(self, message):
        if isinstance(message, bytes):
            self.setup(self.extract_message(message))
        elif isinstance(message, dict):
            self.setup(message)

    def setup(self, message):
        self.MESSAGE_ID = message['msgid'] if 'msgid' in message else uuid.uuid4().hex
        self.MODULE = message['module']
        self.SUBMODULE = message['submodule']
        self.PARAMS = message['data']
        options = message['options'] if 'options' in message else dict()
        options = options if options else dict()
        self.set_message_options(options.copy())

    def set_message(self, module, submodule, message):
        self.MESSAGE_ID = uuid.uuid4().hex
        self.MODULE = module
        self.SUBMODULE = submodule

    def set_parameters(self, *args, **kwargs):
        self.PARAMS = [args, kwargs]

    def get_module_id(self):
        return get_module_id(self.MODULE, self.SUBMODULE)

    def get_message_id(self):
        return self.MESSAGE_ID

    def set_message_options(self, options):
        self.message_options.update(options)

    @property
    def options(self):
        return self.message_options

    def encode(self):
        raise NotImplementedError()

    @classmethod
    def create_message(cls, module, submodule, cmd_evt, *args, **kwargs):
        message_obj = object.__new__(cls)
        message_obj.__init__()
        message_obj.set_message(module, submodule, cmd_evt)
        message_obj.set_parameters(*args, **kwargs)
        return message_obj


class MessageCommand(AbstractMessage):

    def __init__(self, message=None):
        super(MessageCommand, self).__init__(msg_type=MODE_COMMAND)
        self.COMMAND = None
        self.process_message(message)

    def setup(self, message):
        super(MessageCommand, self).setup(message)
        self.COMMAND = message['command']

    def set_message(self, module, submodule, message):
        super(MessageCommand, self).set_message(module, submodule, message)
        self.COMMAND = message

    def encode(self):
        if self.PARAMS is None:
            self.PARAMS = [list(), dict()]
        adict = {'msgtype': self.message_mode,
                 'msgid': self.MESSAGE_ID,
                 'module': self.MODULE,
                 'submodule': self.SUBMODULE,
                 'command': self.COMMAND,
                 'data': self.PARAMS,
                 'options': self.options.copy()}
        command_str = json.dumps(adict)
        return base64.b64encode(command_str.encode("utf-8"))


class MessageEvent(AbstractMessage):

    def __init__(self, message=None):
        super(MessageEvent, self).__init__(msg_type=MODE_EVENT)
        self.EVENT = None
        self.process_message(message)

    def setup(self, message):
        super(MessageEvent, self).setup(message)
        self.EVENT = message['event']

    def set_message(self, module, submodule, message):
        super(MessageEvent, self).set_message(module, submodule, message)
        self.EVENT = message

    def encode(self):
        adict = {'msgtype': self.message_mode,
                 'msgid': self.MESSAGE_ID,
                 'module': self.MODULE,
                 'submodule': self.SUBMODULE,
                 'event': self.EVENT,
                 'data': self.PARAMS,
                 'options': self.options.copy()}
        command_str = json.dumps(adict)
        return base64.b64encode(command_str.encode("utf-8"))

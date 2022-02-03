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

import base64
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


class BaseMessage(object):

    def __init__(self, msg_type=None):
        self.message_mode = msg_type

    @staticmethod
    def extract_message(message):
        msg_bytes = base64.b64decode(message)
        return json.loads(msg_bytes.decode("utf-8"))


class AbstractMessage(BaseMessage):

    def __init__(self, message=None, msg_type=None):
        super(AbstractMessage, self).__init__(msg_type)
        self.MODULE = None
        self.SUBMODULE = None
        self.PARAMS = None
        self.process_message(message)

    def process_message(self, message):
        if isinstance(message, bytes):
            self.do_process(self.extract_message(message))
        elif isinstance(message, dict):
            self.do_process(message)

    def do_process(self, message):
        self.MODULE = message['module']
        self.SUBMODULE = message['submodule']
        self.PARAMS = message['data']

    def setup(self, message):
        self.MODULE = message['module']
        self.SUBMODULE = message['submodule']
        self.PARAMS = message['data']

    def set_parameters(self, *args, **kwargs):
        self.PARAMS = [args, kwargs]

    def get_module_id(self):
        return get_module_id(self.MODULE, self.SUBMODULE)

    def encode(self):
        return None


class MessageCommand(AbstractMessage):

    def __init__(self, message=None):
        super(MessageCommand, self).__init__(MODE_COMMAND)
        self.COMMAND = None
        self.process_message(message)

    def process_message(self, message):
        if isinstance(message, bytes):
            self.do_process(self.extract_message(message))
        elif isinstance(message, dict):
            self.do_process(message)

    def do_process(self, message):
        super(MessageCommand, self).do_process(message)
        self.COMMAND = message['command']

    def setup(self, message):
        super(MessageCommand, self).setup(message)
        self.COMMAND = message['command']

    def set_command(self, module, submodule, command):
        self.MODULE = module
        self.SUBMODULE = submodule
        self.COMMAND = command

    def encode_command(self):
        adict = {'msgtype': self.message_mode,
                 'module': self.MODULE,
                 'submodule': self.SUBMODULE,
                 'command': self.COMMAND,
                 'data': self.PARAMS}
        command_str = json.dumps(adict)
        return base64.b64encode(command_str.encode("utf-8"))

    def encode(self):
        return self.encode_command()


class MessageEvent(AbstractMessage):

    def __init__(self, message=None):
        super(MessageEvent, self).__init__(MODE_EVENT)
        self.EVENT = None
        self.process_message(message)

    def process_message(self, message):
        if isinstance(message, bytes):
            self.do_process(self.extract_message(message))
        elif isinstance(message, dict):
            self.do_process(message)

    def do_process(self, message):
        super(MessageEvent, self).do_process(message)
        self.EVENT = message['event']

    def setup(self, message):
        super(MessageEvent, self).setup(message)
        self.EVENT = message['event']

    def set_event(self, module, submodule, event):
        self.MODULE = module
        self.SUBMODULE = submodule
        self.EVENT = event

    def encode_command(self):
        adict = {'msgtype': self.message_mode,
                 'module': self.MODULE,
                 'submodule': self.SUBMODULE,
                 'event': self.EVENT,
                 'data': self.PARAMS}
        command_str = json.dumps(adict)
        return base64.b64encode(command_str.encode("utf-8"))

    def encode(self):
        return self.encode_command()


class MessageFactory(BaseMessage):

    @classmethod
    def get_class(cls, msg_type):
        klass_list = [MessageCommand, MessageEvent]
        return klass_list[msg_type] if msg_type < len(klass_list) else None

    @classmethod
    def instantiate(cls, klass):
        obj = object.__new__(klass)
        obj.__init__()
        return obj

    @classmethod
    def generate(cls, message):
        cmd_dict = cls.extract_message(message) \
            if isinstance(message, bytes) else message if isinstance(message, dict) else None
        klass = cls.get_class(cmd_dict['msgtype']) if cmd_dict and ('msgtype' in cmd_dict) else None
        obj = cls.instantiate(klass) if klass else None
        obj.setup(cmd_dict) if obj else None
        return obj

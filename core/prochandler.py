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

import logging
from core import msgobject


class BaseCommandProcessor(object):

    def __init__(self):
        self.MODULE = None
        self.SUBMODULE = None
        self._parent = None

    def _get_module_id(self):
        return msgobject.get_module_id(self.MODULE, self.SUBMODULE)

    def _is_mq_method(self, func_name, func_code=None, mq_type=msgobject.MODE_COMMAND):
        """Check if function is a published method"""
        func = getattr(self, func_name, None) if func_code is None else func_code
        return True if (func is not None) and (getattr(func, 'mq_type', msgobject.MODE_COMMAND) == mq_type) else False

    def _perform_mq_exec(self, cmd):
        error_type = 1 if cmd.COMMAND in [None, ''] else 0
        queue_func = getattr(self, cmd.COMMAND, None) if error_type == 0 else None
        if (error_type == 0) and (queue_func is not None) and self._is_mq_method(cmd.COMMAND, queue_func):
            _args, _kwargs = cmd.PARAMS
            logging.debug("executing {0}".format(cmd.COMMAND))
            return queue_func(*_args, **_kwargs)
        return None

    def _perform_mq_notify(self, func, event):
        error_type = 1 if func in [None, ''] else 0
        queue_func = getattr(self, func, None) if error_type == 0 else None
        if (error_type == 0) and (queue_func is not None) and \
                self._is_mq_method(func, queue_func, msgobject.MODE_EVENT):
            _args, _kwargs = event.PARAMS
            logging.debug("notifying {0}".format(func))
            return queue_func(*_args, **_kwargs)
        return None

    def perform_exec(self, command):
        return self._perform_mq_exec(command)

    def perform_notify(self, func, event):
        return self._perform_mq_notify(func, event)

    def set_parent(self, parent):
        self._parent = parent


class CommandProcessor(BaseCommandProcessor):
    pass

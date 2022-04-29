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
import asyncio
import logging
from common.msgobject import AbstractMessage
from core.msgexec import BaseExecutor
from common.prochandler import CommandProcessor


class AsyncModuleExecutor(BaseExecutor):

    def __init__(self, config=None, module=None):
        super(AsyncModuleExecutor, self).__init__(config=config, module=module)
        self.loop = None

    def set_loop(self, loop):
        self.loop = loop

    def assign_task(self, module: CommandProcessor, message_obj: AbstractMessage, func: str = None):
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self.do_execute(module, message_obj, func))

    async def do_execute(self, module: CommandProcessor, message_obj: AbstractMessage, func: str):
        logging.debug("Submitting task {0}".format(message_obj.get_module_id()))
        try:
            queue_func, _args, _kwargs = module.prepare_execution(message_obj, func)
            if queue_func:
                await queue_func(*_args, **_kwargs)
        except Exception as ex:
            logging.exception(ex)

    async def execute_module(self, message_obj: AbstractMessage):
        for module, str_func in self._collect_object_module(message_obj):
            self.assign_task(module, message_obj, str_func)

    def submit_task(self, message_obj):
        ...

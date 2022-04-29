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

try:
    import pybase64 as base64
except:
    import base64

import logging
import os
import asyncio
from asyncio import StreamReader, StreamReaderProtocol
from core.msgpexec import BaseProcessExecutor
from core.aio.aiomsgexec import AsyncModuleExecutor
from core.aio.aiomsgfactory import AsyncMessageFactory


class AsyncExecutor(object):

    def __init__(self):
        self._handler = None

    @staticmethod
    async def perform_decoding(message: str) -> bytes:
        message = message.encode("utf-8") if isinstance(message, str) else message
        return base64.b64decode(message)

    async def handle_message(self, message):
        message_object = AsyncMessageFactory.generate(await self.perform_decoding(message)) if message else None
        return_val = message_object and message_object.message_mode == 999
        if not return_val:
            if message_object:
                await self._handler.execute_module(message_object)
            else:
                logging.error("Could not extract message correctly: {0}".format(message))
        return return_val

    def async_stop(self):
        pass

    def initialize_handler(self):
        self._handler = AsyncModuleExecutor(self._get_configuration(), self._get_module())
        self._handler.set_properties(self._get_command_properties(), self._get_event_properties())
        self._handler.set_module_configuration(self._get_module_configuration())
        self._handler.set_loop(self._get_loop())
        self._handler.configure()

    async def read_message(self, read_fd):
        should_terminate = False
        loop = asyncio.get_running_loop()
        reader = StreamReader()
        protocol = StreamReaderProtocol(reader)
        transport, _ = await loop.connect_read_pipe(lambda: protocol, os.fdopen(read_fd, 'rb', 0))
        while True:
            try:
                message = await reader.readline()
                should_terminate = isinstance(message, str) and (message.strip().lower() == 'shut')
                if not should_terminate:
                    if message and (len(message) > 0):
                        should_terminate = await self.handle_message(message)
                    else:
                        await asyncio.sleep(1)
                if should_terminate:
                    break
            except Exception as ex:
                logging.error(ex)
            finally:
                self.async_stop() if should_terminate else None

    def _get_configuration(self):
        raise NotImplementedError()

    def _get_module(self):
        raise NotImplementedError()

    def _get_command_properties(self):
        raise NotImplementedError()

    def _get_event_properties(self):
        raise NotImplementedError()

    def _get_module_configuration(self):
        raise NotImplementedError()

    def _get_loop(self):
        raise NotImplementedError()


class AsyncProcessExecutor(BaseProcessExecutor, AsyncExecutor):
    """
    Process based (aio) message execution manager
    """

    def __init__(self, config=None, module=None):
        super(AsyncProcessExecutor, self).__init__(config=config, module=module)
        self.read_fd = None
        self.write_fd = None
        self.loop = None
        self.writer_transport = None

    def do_configure(self):
        super(AsyncProcessExecutor, self).do_configure()
        self.read_fd, self.write_fd = os.pipe()

    def do_start(self):
        self.writer_transport = os.fdopen(self.write_fd, 'wb', 0)
        os.set_inheritable(self.read_fd, True)
        super(AsyncProcessExecutor, self).do_start()
        os.close(self.read_fd)
        
    def do_stop(self):
        super(AsyncProcessExecutor, self).do_stop()
        self.writer_transport.close()

    def submit_task(self, message_obj):
        self.writer_transport.write("{0}\n".format(message_obj.encode().decode("utf-8")).encode())

    def subprocess_entry(self):
        self.initialize_handler()
        os.close(self.write_fd)
        self.loop = asyncio.get_event_loop()
        try:
            self.loop.run_until_complete(self.read_message(self.read_fd))
        finally:
            self.loop.close()

    def _get_configuration(self):
        return self.get_configuration()

    def _get_module(self):
        return self.get_module()

    def _get_command_properties(self):
        return self.get_command_properties()

    def _get_event_properties(self):
        return self.get_event_properties()

    def _get_module_configuration(self):
        return self.get_module_configuration()

    def _get_loop(self):
        return self.loop



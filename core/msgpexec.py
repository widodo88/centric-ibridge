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
import multiprocessing as mp
from core.msgobject import AbstractMessage
from core.msgexec import ModuleExecutor, MessageExecutionManager


class ProcessExecutor(ModuleExecutor):

    def __init__(self, config=None, module=None, workers=4):
        super(ProcessExecutor, self).__init__(config=config, module=module, workers=workers)
        self._queue = None
        self._process = None

    def do_configure(self):
        super(ProcessExecutor, self).do_configure()
        self._queue = mp.Queue()
        self._process = mp.Process(target=self.daemonize_process)

    def do_start(self):
        super(ProcessExecutor, self).do_start()
        self._process.start()

    def submit_task(self, message_obj: AbstractMessage):
        if self.has_service(message_obj):
            self._queue.put(message_obj)
        else:
            logging.error("Could not parse message correctly")

    def daemonize_process(self):
        while self.is_running():
            try:
                message_obj = self._queue.get(True, 1)
                if message_obj and isinstance(message_obj, AbstractMessage):
                    self.execute_module(message_obj)
            except:
                time.sleep(0.1)


class ProcessMessageExecutionManager(MessageExecutionManager):

    def __init__(self, config):
        super(ProcessMessageExecutionManager, self).__init__(config=config, klass=ProcessExecutor)


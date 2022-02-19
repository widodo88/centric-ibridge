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
import logging
import traceback
from telegram.ext import Updater
from threading import RLock
from common import consts
from core.startable import Startable, LifeCycleManager


class TelegramProvider(Startable):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    def __init__(self, config=None):
        super(TelegramProvider, self).__init__(config=config)
        self._telegram: Updater = None

    def do_configure(self):
        assert self.service_enabled, "Telegram has not been enabled"
        token = self.get_config_value(consts.TELEGRAM_TOKEN, None)
        service_enabled = token not in ['', None]
        self.service_enabled = service_enabled
        assert service_enabled, "Telegram token is not provided, could not configure"
        self._telegram = Updater(token)

    def get_telegram(self):
        return self._telegram

    def do_stop(self):
        if self._telegram:
            try:
                if self._telegram.running or self._telegram.dispatcher.has_running_threads:
                    self._telegram.stop()
                    self._telegram.idle()
            except:
                logging.error(traceback.format_exc())

    @classmethod
    def get_default_instance(cls):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()
            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()


class TelegramPreparer(object):

    @classmethod
    def prepare_telegram(cls, cfg: dict, server_holder: LifeCycleManager):
        telegram_enabled = server_holder.get_config_value(consts.TELEGRAM_ENABLED, "false")
        telegram_enabled = True if telegram_enabled.lower() == "true" else False
        if telegram_enabled:
            telegram_instance = TelegramProvider.get_default_instance()
            if not telegram_instance.is_configured():
                telegram_instance.set_configuration(cfg)
                telegram_instance.service_enabled = True
                server_holder.add_object(telegram_instance)

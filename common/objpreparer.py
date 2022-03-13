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
import typing as t
from common.startable import Startable, SingletonObject, LifeCycleManager


class BaseObjectProvider(Startable, SingletonObject):
    ...


class BaseObjectPreparer(object):

    @classmethod
    def _get_provider_klass(cls) -> t.Type[BaseObjectProvider]:
        return BaseObjectProvider

    @classmethod
    def _service_enabled_name(cls):
        return NotImplementedError()

    @classmethod
    def is_service_enabled(cls, server_holder: LifeCycleManager):
        service_enabled = server_holder.get_config_value(cls._service_enabled_name(), "false")
        return True if service_enabled.lower() == "true" else False

    @classmethod
    def prepare(cls, cfg: dict, server_holder: LifeCycleManager):
        if cls.is_service_enabled(server_holder):
            klass: t.Type[BaseObjectProvider] = cls._get_provider_klass()
            provider_instance = klass.get_default_instance()
            if not provider_instance.is_configured():
                provider_instance.set_configuration(cfg)
                provider_instance.service_enabled = True
                server_holder.add_object(provider_instance)

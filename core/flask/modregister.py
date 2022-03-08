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
from flask_restx import Api
from common.objloader import ObjectLoader
from common.singleton import SingletonObject


class ModuleRegisterer(ObjectLoader, SingletonObject):

    @classmethod
    def register_module(cls, api: Api, modules: list):
        instance = cls.get_default_instance()
        for mod_name in modules:
            try:
                mod = instance._get_klass(mod_name)
                api.register_module(mod)
            except:
                logging.exception(traceback.format_exc())




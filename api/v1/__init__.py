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
from common import consts
from api.v1.extensions import flask_api
from core.baserestsrv import BaseRestServer
from core.flask.modregister import ModuleRegisterer


def register_rest_modules(app_srv: BaseRestServer):
    config = app_srv.get_configuration()
    rest_services = config[consts.RESTAPI_AVAILABLE_SERVICES] if \
        consts.RESTAPI_AVAILABLE_SERVICES in config else None
    rest_services = rest_services if rest_services else ""
    rest_services = [service.strip() for service in rest_services.split(",") if service.strip() not in [None, '']]
    ModuleRegisterer.register_module(flask_api, rest_services)


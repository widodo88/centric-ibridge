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
from core.baseappsrv import BaseAppServer


class Configuration(object):

    SQLALCHEMY_BINDS = dict()


def register_rest_databases(app_srv: BaseAppServer):
    config = app_srv.get_configuration()
    rest_databases = config[consts.RESTAPI_AVAILABLE_DATABASES] if \
        consts.RESTAPI_AVAILABLE_DATABASES in config else None
    rest_databases = rest_databases if rest_databases else ""
    rest_databases = [service.strip() for service in rest_databases.split(",") if service.strip() not in [None, '']]
    for database in rest_databases:
        key, value = database.split('=', 1)
        Configuration.SQLALCHEMY_BINDS[key] = value



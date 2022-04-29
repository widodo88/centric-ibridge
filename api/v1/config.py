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
import json
import decimal
from common import consts
from core.baseappsrv import BaseAppServer
from sqlalchemy.dialects import registry


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DecimalEncoder, self).default(o)


class Configuration(object):

    SQLALCHEMY_BINDS = dict()
    RESTX_JSON = dict()


def register_rest_databases(app_srv: BaseAppServer):
    registry.register("ibmdb2", "core.ext.sqladialect.ibm_db_sa.ibm_db", "DB2Dialect_ibm_db")
    config = app_srv.get_configuration()
    rest_databases = config[consts.RESTAPI_AVAILABLE_DATABASES] if \
        consts.RESTAPI_AVAILABLE_DATABASES in config else None
    rest_databases = rest_databases if rest_databases else ""
    rest_databases = [service.strip() for service in rest_databases.split(",") if service.strip() not in [None, '']]
    for database in rest_databases:
        key, value = database.split('=', 1)
        Configuration.SQLALCHEMY_BINDS[key] = value
    Configuration.RESTX_JSON['cls'] = DecimalEncoder




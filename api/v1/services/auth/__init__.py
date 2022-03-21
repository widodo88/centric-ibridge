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
from flask_restx import Api
from core.restprep import RESTModulePreparer
from api.v1.services.auth.namespace import ns

# importing modules
import api.v1.services.auth.endpoint


class AuthModulePreparer(RESTModulePreparer):

    def __init__(self, config=None):
        super(AuthModulePreparer, self).__init__(config=config)

    def do_configure(self):
        super(AuthModulePreparer, self).do_configure()

    def prepare_router(self, api: Api):
        api.add_namespace(ns, '/auth')

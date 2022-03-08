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
import os
from flask import Flask
from common import consts
from core.flask.flaskapi import FlaskApi
from typing import Optional
from core.baseappsrv import BaseAppServer
from common.objloader import ObjectLoader


class BaseRestServer(BaseAppServer, ObjectLoader):

    def __init__(self):
        super(BaseRestServer, self).__init__()
        self.rest_app: Optional[Flask] = None
        self.rest_api: Optional[FlaskApi] = None

    def set_rest_api(self, api: FlaskApi):
        self.rest_api = api
        if self.rest_api:
            config = self.get_configuration()
            self.rest_api.set_configuration(config)
            self.rest_api.configure()

    def get_rest_app(self):
        self.configure()
        return self.rest_app

    __call__ = get_rest_app

    def set_rest_app(self, app: Flask):
        self.rest_app = app

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
import typing
from flask_restx import Api, Namespace
from core.restprep import RESTModulePreparer
from common.configurable import Configurable


class PrefixMiddleware(object):

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]


class FlaskApi(Configurable, Api):

    def __init__(self, config=None, **kwargs):
        super(FlaskApi, self).__init__(**kwargs)

    def set_prefix(self, prefix):
        self.prefix = prefix

    def set_title(self, title):
        self.title = title

    def register_module(self, klass):
        config = self.get_configuration()
        if isinstance(klass, Namespace):
            self.add_namespace(klass)
        elif klass and (issubclass(klass, RESTModulePreparer) or isinstance(klass, RESTModulePreparer)):
            klass.register_api_router(config, self)

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
import re
import sys
import logging
import api
import datetime as dt
from dotenv import dotenv_values
from common import consts
from flask import Flask, redirect, _request_ctx_stack
from flask_jwt_extended import create_access_token, set_access_cookies
from flask_jwt_extended import get_jwt_identity
from werkzeug.middleware.proxy_fix import ProxyFix
from multiprocessing_logging import install_mp_handler
from core.baserestsrv import BaseRestServer
from core.redisprovider import RedisPreparer
from core.ext.minioprovider import MinioPreparer
from core.flask.flaskapi import PrefixMiddleware
from logging.handlers import TimedRotatingFileHandler
from api import register_rest_modules
from api import RootApiResource


class RestApp(BaseRestServer):

    def do_configure(self):
        super(RestApp, self).do_configure()
        config = self.get_configuration()        
        consts.DEFAULT_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
        RedisPreparer.prepare(config, self)
        MinioPreparer.prepare(config, self)
        rest_app = Flask("iBridge Server",
                         root_path='/',
                         static_url_path="/static",
                         static_folder=os.path.join(consts.DEFAULT_SCRIPT_PATH, "resources/static"))
        rest_app.wsgi_app = PrefixMiddleware(rest_app.wsgi_app,
                                             prefix=self.get_config_value(consts.RESTAPI_ROOT_PATH, '/'))
        rest_app.wsgi_app = ProxyFix(rest_app.wsgi_app)
        rest_app.add_url_rule('/', None, self.root_index)
        rest_app.after_request_funcs.setdefault(None, []).append(self.refresh_token)
        self.set_rest_app(rest_app)
        api.ExtensionConfigurator.configure_extensions(self)
        register_rest_modules(self)

    def root_index(self):
        return redirect(self.rest_api.url_for(RootApiResource))

    @staticmethod
    def refresh_token(response):
        decoded_jwt = getattr(_request_ctx_stack.top, "jwt", None)
        if decoded_jwt:
            try:
                exp_timestamp = decoded_jwt["exp"]
                now = dt.datetime.now(dt.timezone.utc)
                target_timestamp = dt.datetime.timestamp(now + dt.timedelta(minutes=30))
                if target_timestamp > exp_timestamp:
                    access_token = create_access_token(identity=get_jwt_identity())
                    set_access_cookies(response, access_token)
            except (RuntimeError, KeyError):
                pass
        return response

    def do_start(self):
        super(RestApp, self).do_start()
        rest_app = self.get_rest_app()
        rest_app.run(host="127.0.0.1", port=8080, debug=not consts.IS_PRODUCTION_MODE)


def configure_logging(config):
    default_level = consts.log_level[config[consts.LOG_LEVEL]] if consts.LOG_LEVEL in config \
        else consts.DEFAULT_LOG_LEVEL
    log_format = config[consts.LOG_FORMAT] if consts.LOG_FORMAT in config else consts.DEFAULT_LOG_FORMAT
    log_date_format = consts.DEFAULT_LOG_DATE_FORMAT
    log_file = config[consts.RESTAPI_LOG_FILE] if consts.RESTAPI_LOG_FILE in config else consts.DEFAULT_RESTAPI_LOG_FILE
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=5)
    logging.basicConfig(format=log_format, datefmt=log_date_format, handlers=[handler], level=default_level)
    install_mp_handler()


def create_app():
    consts.prepare_path()
    config = dotenv_values("{0}/.env".format(consts.DEFAULT_SCRIPT_PATH))
    configure_logging(config)
    rest_app_instance = RestApp.get_default_instance()
    rest_app_instance.set_configuration(config)
    return rest_app_instance()


app: Flask = create_app()

if __name__ == '__main__':
    is_debug = not consts.IS_PRODUCTION_MODE
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(RestApp.get_default_instance().start())

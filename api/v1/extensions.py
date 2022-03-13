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
import base64
from common import consts
from core.flask.flaskapi import FlaskApi
from core.flask.redsession import FlaskRedisSession
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
from core.baseappsrv import BaseAppServer
from api.mainresource import RootApiResource
from api.v1.security.ldapauth import LDAPAuthService
from core.redisprovider import RedisPreparer

authorization = {"Bearer": {"type": "apiKey",
                            "in": "header",
                            "name": "access_token"
                            }
                 }

flask_api = FlaskApi(doc='/docs', version='1.0',
                     default='API: Default',
                     default_label='root')

cors = CORS()
marshmallow = Marshmallow()
jwt = JWTManager()
authenticator = LDAPAuthService.get_default_instance()
redis_session = FlaskRedisSession()


# Register a callback function that loads a user from your database whenever
# a protected route is accessed. This should return any python object on a
# successful lookup, or None if the lookup failed for any reason (for example
# if the user has been deleted from the database).
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["user"]
    return identity


class ExtensionConfigurator(object):

    @classmethod
    def configure_extensions(cls, main_app: BaseAppServer):
        app = main_app.get_rest_app()
        config = main_app.get_configuration()
        cors.init_app(app)
        redis_session.redis_enabled = RedisPreparer.is_service_enabled(main_app)
        redis_session.init_app(app)
        marshmallow.init_app(app)
        secret_key = config[consts.RESTAPI_SECRET_KEY] if consts.RESTAPI_SECRET_KEY in config else None
        secret_key = secret_key if secret_key else base64.b64encode(os.urandom(32)).decode("utf-8")
        app.config['SECRET_KEY'] = base64.b64decode(secret_key)
        app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
        app.config['JWT_REFRESH_COOKIE_NAME'] = 'refresh_token'
        jwt.init_app(app)
        authenticator.set_configuration(config)
        authenticator.configure()
        flask_api.set_configuration(config)
        flask_api.set_title('iBridge REST API Server')
        flask_api.set_prefix('/api/v1')
        flask_api.default_namespace.add_resource(RootApiResource, '/')
        flask_api.init_app(app)
        main_app.set_rest_api(flask_api)



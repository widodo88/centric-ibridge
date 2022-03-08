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
from http import HTTPStatus
from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from api.v1.extensions import authenticator
from utils import restutils
from .schema import LoginSchema
from flask_jwt_extended import (
    config, set_access_cookies, create_access_token, create_refresh_token)

ns = Namespace('API: Authorization', 'Authorize access to API service')
login_schema = LoginSchema()

auth_login = ns.model(
    "Login data",
    {
        "username": fields.String(required=True),
        "password": fields.String(required=True),
    },
)

login_success = ns.model(
    "Auth success response",
    {
        "status": fields.Boolean,
        "message": fields.String,
        "access_token": fields.String,
        "expires_in": fields.Integer,
        "token_type": fields.String
    })


@ns.route('/login', endpoint='auth_login')
class LoginResource(Resource):
    @ns.expect(auth_login, validate=True)
    @ns.doc("Auth Login",
            responses={
                int(HTTPStatus.OK): ("Logged in", login_success),
                int(HTTPStatus.BAD_REQUEST): "Validation error",
                int(HTTPStatus.UNAUTHORIZED): "Incorrect password or incomplete credentials.",
                int(HTTPStatus.INTERNAL_SERVER_ERROR): "username does not match any account."
            })
    def post(self):
        """ Login using username and password """
        login_data = request.get_json()
        if errors := login_schema.validate(login_data):
            return restutils.validation_error(False, errors), int(HTTPStatus.BAD_REQUEST)
        login_result, user_info = authenticator.login(login_data)
        if not login_result:
            return restutils.err_resp("Incorrect password or incomplete credentials", "authentication_error", 401)

        user_claim = [(key, value) for key, value in user_info.items() if key in ['fullname', 'email']]
        access_token = create_access_token(identity=login_data['username'], additional_claims={'user': dict(user_claim)})
        resp = restutils.message(True, "Logged in")
        resp['access_token'] = access_token
        resp['expires_in'] = config.config.access_expires.seconds
        resp['token_type'] = config.config.header_type
        response = jsonify(resp)
        if 'access_token' in resp:
            set_access_cookies(response, resp.get('access_token'))
        return response




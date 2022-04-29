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
import ldap
import logging
from typing import Optional
from common import consts
from core.flask.baseauthsvc import BaseAuthService
from flask_jwt_extended import JWTManager


class LDAPAuthService(BaseAuthService):

    def __init__(self, config=None):
        super(BaseAuthService, self).__init__(config=config)
        self.ldap_address: Optional[str] = None
        self.ldap_prefix: Optional[str] = None
        self.ldap_suffix: Optional[str] = None
        self.ldap_bind_dn: Optional[str] = None
        self.ldap_bind_password: Optional[str] = None
        self.jwt_manager: Optional[JWTManager] = None

    def set_jwt_manager(self, jwt: JWTManager):
        self.jwt_manager = jwt

    def do_configure(self):
        self.ldap_address = self.get_config_value(consts.LDAP_ADDRESS, 'ldap://localhost')
        self.ldap_prefix = self.get_config_value(consts.LDAP_USER_PREFIX, None)
        self.ldap_suffix = self.get_config_value(consts.LDAP_USER_SUFFIX, None)
        self.ldap_bind_dn = self.get_config_value(consts.LDAP_BIND_DN, None)
        self.ldap_bind_password = self.get_config_value(consts.LDAP_BIND_PASSWD, None)
        if self.jwt_manager:
            # Register a callback function that loads a user from LDAP whenever
            # a protected route is accessed. This should return any python object on a
            # successful lookup, or None if the lookup failed for any reason (for example
            # if the user has been deleted from the database).
            self.jwt_manager._user_lookup_callback = self.user_lookup_callback

    def user_lookup_callback(self, _jwt_header, jwt_data):
        username = jwt_data['sub']
        identity = self.get_user_info(username)
        return identity

    def get_user_info(self, username):
        result = dict()
        if username is None:
            return result
        conn = ldap.initialize(self.ldap_address)
        try:
            conn.simple_bind_s(self.ldap_bind_dn, self.ldap_bind_password)
            resp = conn.search_s(self.ldap_suffix, ldap.SCOPE_SUBTREE, "({}={})".format(self.ldap_prefix, username))
            resp = resp[0][1]
            result.update([('username', username),
                           ('fullname', resp['displayName'][0].decode()),
                           ('email', resp['mail'][0].decode())])
        finally:
            conn.unbind_s() if conn else None
        return result

    def perform_login(self, login_data: dict):
        login_result = True
        conn = None
        result = dict()
        try:
            username = login_data['username']
            password = login_data['password']
            conn = ldap.initialize(self.ldap_address)
            conn.simple_bind_s('{}={},{}'.format(self.ldap_prefix, username, self.ldap_suffix), password)
            resp = conn.search_s(self.ldap_suffix, ldap.SCOPE_SUBTREE, "({}={})".format(self.ldap_prefix, username))
            resp = resp[0][1]
            result.update([('username', username),
                           ('fullname', resp['displayName'][0].decode()),
                           ('email', resp['mail'][0].decode())])
        except Exception as ex:
            logging.debug(ex)
            login_result = False
        finally:
            conn.unbind_s() if conn else None
        return login_result, result

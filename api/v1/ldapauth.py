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
from typing import Optional
from common import consts
from core.flask.baseauthsvc import BaseAuthService


class LDAPAuthService(BaseAuthService):

    def __init__(self, config=None):
        super(BaseAuthService, self).__init__(config=config)
        self.ldap_address: Optional[str] = None
        self.ldap_prefix: Optional[str] = None
        self.ldap_suffix: Optional[str] = None

    def do_configure(self):
        self.ldap_address = self.get_config_value(consts.LDAP_ADDRESS, 'ldap://localhost')
        self.ldap_prefix = self.get_config_value(consts.LDAP_USER_PREFIX, None)
        self.ldap_suffix = self.get_config_value(consts.LDAP_USER_SUFFIX, None)

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
        except:
            login_result = False
        finally:
            conn.unbind_s() if conn else None
        return login_result, result

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
from common.configurable import Configurable
from common.singleton import SingletonObject
from utils.restutils import err_resp


class BaseAuthService(Configurable, SingletonObject):

    def perform_login(self, login_data: dict):
        raise NotImplementedError()

    def login(self, login_data: dict):
        if not login_data:
            return err_resp("Login information must be provided", "bad_login", 400)
        return self.perform_login(login_data)








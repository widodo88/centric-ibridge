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

from fastapi import FastAPI, Depends
from core.restprep import RESTModulePreparer
from restsvc.users.model import UserDB
from restsvc.users.activeusr import current_active_user


class ExampleRouterPreparer(RESTModulePreparer):

    def __init__(self):
        super(ExampleRouterPreparer, self).__init__()

    def do_configure(self):
        super(ExampleRouterPreparer, self).do_configure()

    def prepare_router(self, app: FastAPI):

        @app.get("/hello")
        async def hello_user(user: UserDB = Depends(current_active_user)):
            return {"message": f"Hello {user.email}!"}






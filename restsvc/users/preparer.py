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

from common import consts
from fastapi import FastAPI, Depends, APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from fastapi_users.authentication import BearerTransport
from fastapi_users.authentication import JWTStrategy
from core.restprep import RESTModulePreparer
from fastapi_users.db import SQLAlchemyUserDatabase
from restsvc.users.model import User, UserCreate, UserDB, UserUpdate
from restsvc.users.users import UserManager
from restsvc.users.dbengine import create_db_and_tables, get_user_db


class UserRouterPreparer(RESTModulePreparer):

    def __init__(self):
        super(UserRouterPreparer, self).__init__()
        self._secret_key = None

    def do_configure(self):
        config = self.get_configuration()
        self._secret_key = config[consts.RESTAPI_SECRET_KEY] if consts.RESTAPI_SECRET_KEY in config else None
        super(UserRouterPreparer, self).do_configure()

    def prepare_router(self, app: FastAPI):
        def get_jwt_strategy() -> JWTStrategy:
            return JWTStrategy(secret=self._secret_key, lifetime_seconds=3600)

        async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
            yield UserManager(user_db, self._secret_key)

        bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
        auth_backend = AuthenticationBackend(name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy)
        app_users = FastAPIUsers(get_user_manager, [auth_backend], User, UserCreate, UserUpdate, UserDB)
        app.include_router(app_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
        app.include_router(app_users.get_register_router(), prefix="/auth", tags=["auth"])
        app.include_router(app_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
        app.include_router(app_users.get_verify_router(), prefix="/auth", tags=["auth"])
        app.include_router(app_users.get_users_router(), prefix="/users", tags=["users"])

        current_active_user = app_users.current_user(active=True)

        @app.get("/authenticated-route")
        async def authenticated_route(user: UserDB = Depends(current_active_user)):
            return {"message": f"Hello {user.email}!"}

        @app.on_event("startup")
        async def on_startup():
            # Not needed if you setup a migration system like Alembic
            await create_db_and_tables()

        return app

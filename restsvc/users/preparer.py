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

from typing import Type
from common import consts
from fastapi import FastAPI, Depends, APIRouter, status, HTTPException, Request
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend
from fastapi_users.authentication import BearerTransport
from fastapi_users.authentication import JWTStrategy
from fastapi_users.router.common import ErrorCode, ErrorModel
from fastapi_users.manager import BaseUserManager, UserManagerDependency, InvalidPasswordException, UserAlreadyExists
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users import models
from restsvc.users.model import User, UserCreate, UserDB, UserUpdate
from restsvc.users.users import UserManager
from restsvc.users.dbengine import create_db_and_tables, get_user_db
from core.restprep import RESTModulePreparer


class UserRouterPreparer(RESTModulePreparer):

    def __init__(self):
        super(UserRouterPreparer, self).__init__()
        self._secret_key = None
        self._app_user = None
        self._admin_user = None

    def do_configure(self):
        config = self.get_configuration()
        self._secret_key = config[consts.RESTAPI_SECRET_KEY] if consts.RESTAPI_SECRET_KEY in config else None
        self._admin_user = config[consts.RESTAPI_ADMIN_USERNAME] if consts.RESTAPI_ADMIN_USERNAME in config else None
        super(UserRouterPreparer, self).do_configure()

    def prepare_router(self, app: FastAPI):
        def get_jwt_strategy() -> JWTStrategy:
            return JWTStrategy(secret=self._secret_key, lifetime_seconds=3600)

        async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
            yield UserManager(user_db, self._secret_key)

        bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
        auth_backend = AuthenticationBackend(name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy)
        self._app_user = FastAPIUsers(get_user_manager, [auth_backend], User, UserCreate, UserUpdate, UserDB)
        app.include_router(self._app_user.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
        self.include_user_registration(app, get_user_manager)

        @app.on_event("startup")
        async def on_startup():
            # Not needed if you setup a migration system like Alembic
            await create_db_and_tables()

    def include_user_registration(self, app: FastAPI, get_user_manager: UserManagerDependency[models.UC, models.UD]):
        def get_register_router(
                user_mgr: UserManagerDependency[models.UC, models.UD],
                user_model: Type[models.U],
                user_create_model: Type[models.UC]
        ) -> APIRouter:
            """Generate a router with the register route."""
            router = APIRouter()

            @router.post(
                "/register",
                response_model=user_model,
                status_code=status.HTTP_201_CREATED,
                name="register:register",
                responses={
                    status.HTTP_400_BAD_REQUEST: {
                        "model": ErrorModel,
                        "content": {
                            "application/json": {
                                "examples": {
                                    ErrorCode.REGISTER_USER_ALREADY_EXISTS: {
                                        "summary": "A user with this email already exists.",
                                        "value": {
                                            "detail": ErrorCode.REGISTER_USER_ALREADY_EXISTS
                                        },
                                    },
                                    ErrorCode.REGISTER_INVALID_PASSWORD: {
                                        "summary": "Password validation failed.",
                                        "value": {
                                            "detail": {
                                                "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                                                "reason": "Password should be"
                                                          "at least 3 characters",
                                            }
                                        },
                                    },
                                }
                            }
                        },
                    },
                },
            )
            async def register(
                    request: Request,
                    user: user_create_model,  # type: ignore
                    user_manager: BaseUserManager[models.UC, models.UD] = Depends(user_mgr),
                    current_user: UserDB = Depends(self.current_active_user)
            ):
                config = self.get_configuration()
                admin_user = config[consts.RESTAPI_ADMIN_USERNAME] if consts.RESTAPI_ADMIN_USERNAME in config else None
                if (not admin_user) or (current_user.email != admin_user):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="NOT_ALLOWED",
                    )
                try:
                    created_user = await user_manager.create(user, safe=True, request=request)
                except UserAlreadyExists:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
                    )
                except InvalidPasswordException as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                            "reason": e.reason,
                        },
                    )

                return created_user

            return router

        if self.has_admin_user():
            app.include_router(get_register_router(get_user_manager, User, UserCreate), prefix="/auth", tags=["auth"])
        else:
            app.include_router(self._app_user.get_register_router(), prefix="/auth", tags=["auth"])

        # app.include_router(self._app_user.get_reset_password_router(), prefix="/auth", tags=["auth"])
        app.include_router(self._app_user.get_verify_router(), prefix="/auth", tags=["auth"])
        app.include_router(self._app_user.get_users_router(), prefix="/users", tags=["users"],
                           responses={404: {"description": "Not found"}})

    def has_admin_user(self):
        return self._admin_user is not None

    def get_app_user(self):
        return self._app_user

    @property
    def current_active_user(self):
        return self._app_user.current_user(active=True) if self._app_user else None

from typing import Optional

from fastapi import Request
from fastapi_users.db import BaseUserDatabase
from fastapi_users import BaseUserManager
from fastapi_users import models
from restsvc.users.model import UserCreate, UserDB


class UserManager(BaseUserManager[UserCreate, UserDB]):
    user_db_model = UserDB

    def __init__(self, user_db: BaseUserDatabase[models.UD], secret: str):
        super(UserManager, self).__init__(user_db)
        self.reset_password_token_secret = secret
        self.verification_token_secret = secret

    async def on_after_register(self, user: UserDB, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


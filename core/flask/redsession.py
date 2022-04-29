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
import re
import typing as t
import time
from datetime import datetime, timedelta
from uuid import uuid4
from redis import ReadOnlyError
from flask import Flask, Response, Request
from flask.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict
from core.redisprovider import RedisProvider

try:
    import ujson as json
except:
    import json


SESSION_EXPIRY_MINUTES = 60
SESSION_COOKIE_NAME = "session"


def utctimestamp_by_second(utc_date_time):
    return int((utc_date_time.replace(tzinfo=time.timezone.utc)).timestamp())


class RedisSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new: bool = False):
        super(RedisSession, self).__init__(initial=initial, on_update=self.on_update)
        self.sid = sid
        self.modified = False
        self.new = new

    @staticmethod
    def on_update(obj: object) -> None:
        if obj:
            obj.modified = True


class RedisSessionInterface(SessionInterface):

    def save_session(self, app: Flask, session: SessionMixin, response: Response) -> None:
        user_id = session.get('user_id')

        if ((not session) and session.modified) or (not user_id):
            self._clean_session(app, response, session)
            return

        redis_value = json.dumps(dict(session))
        expiry_duration = self._get_expiry_duration(app, session)
        expiry_date = datetime.utcnow() + expiry_duration
        expires_in_seconds = int(expiry_duration.total_seconds())

        session.sid = self._set_user_id(session.sid, user_id)
        session_key = self._create_session_key(session.sid, expiry_date)

        with self._get_redis() as redis_obj:
            self._write_wrapper(redis_obj, redis_obj.setex, self._redis_key(session.sid), redis_value, expires_in_seconds)
        response.set_cookie(SESSION_COOKIE_NAME, session_key, expires=expiry_date,
                            httponly=True, domain=self.get_cookie_domain(app))

    def open_session(self, app: Flask, request: Request) -> t.Optional[SessionMixin]:
        session_key = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_key:
            return self._new_session()

        sid, expiry_timestamp = self._extract_session_id(session_key)
        if not expiry_timestamp:
            return self._new_session()

    @staticmethod
    def _new_session():
        return RedisSession(sid=uuid4().hex, new=True)

    @staticmethod
    def _get_expiry_duration(app, session):
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(minutes=SESSION_EXPIRY_MINUTES)

    @staticmethod
    def _redis_key(sid):
        return 's:{}'.format(sid)

    @staticmethod
    def _write_wrapper(redis_obj, write_method, *args):
        for i in range(3):
            try:
                write_method(*args)
                break
            except ReadOnlyError:
                redis_obj.connection_pool.reset()
                time.sleep(1)

    def _get_redis_value_and_ttl_of(self, sid):
        redis_key = self._redis_key(sid)
        with self._get_redis() as redis_obj:
            pipeline = redis_obj.pipeline()
            pipeline.get(redis_key)
            pipeline.ttl(redis_key)
            results = pipeline.execute()
        return tuple(results)

    @staticmethod
    def _expiry_timestamp_not_match(expiry_timestamp, redis_key_ttl):
        datetime_from_ttl = datetime.utcnow() + timedelta(seconds=redis_key_ttl)
        timestamp_from_ttl = utctimestamp_by_second(datetime_from_ttl)
        try:
            return abs(int(expiry_timestamp) - timestamp_from_ttl) > 10
        except (ValueError, TypeError):
            return True

    @staticmethod
    def _extract_session_id(session_key):
        matched = re.match(r"^(.+)\.(\d+)$", session_key)
        if not matched:
            return session_key, None

        return matched.group(1), matched.group(2)

    @staticmethod
    def _create_session_key(sid, expiry_date):
        return "{}.{}".format(sid, utctimestamp_by_second(expiry_date))

    @staticmethod
    def _set_user_id(sid, user_id):
        prefix = "{}.".format(user_id)
        if not sid.startswith(prefix):
            sid = prefix + sid
        return sid

    def _clean_session(self, app, response, session):
        with self._get_redis() as redis_obj:
            self._write_wrapper(redis_obj, redis_obj.delete, self._redis_key(session.session_id))
        response.delete_cookie(SESSION_COOKIE_NAME, domain=self.get_cookie_domain(app))

    @staticmethod
    def _get_redis():
        redis_obj = RedisProvider.get_redis()
        try:
            yield redis_obj
        finally:
            redis_obj.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FlaskRedisSession(object):

    def __init__(self, redis_enabled: bool = False):
        self.redis_enabled = redis_enabled

    def init_app(self, app: Flask):
        if self.redis_enabled:
            session_interface = RedisSessionInterface()
            app.session_interface = session_interface


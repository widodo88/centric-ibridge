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
import typing as t
from redis import Redis
from redis.connection import Connection, ConnectionPool
from common import consts
from common.objpreparer import BaseObjectProvider, BaseObjectPreparer


class RedisProvider(BaseObjectProvider):

    def __init__(self, config=None):
        super(RedisProvider, self).__init__(config=config)
        self._pool = None
        self.service_enabled = False

    def do_configure(self):
        redis_url = self.get_config_value(consts.REDIS_URL, '')
        assert self.service_enabled, "Redis has not been enabled"
        service_enabled = redis_url not in ['', None]
        self.service_enabled = service_enabled
        assert service_enabled, "Redis URL is not provided, could not configure"
        self._pool = ConnectionPool.from_url(redis_url)

    def do_stop(self):
        self._pool.disconnect(inuse_connections=True)

    def get_pool(self):
        return self._pool

    def get_connection(self, command_name, *keys, **options):
        return self._pool.get_connection(command_name, *keys, **options)

    def release_connection(self, connection: Connection):
        self._pool.release(connection)

    def get_redis(self):
        return Redis(connection_pool=self._pool)


class RedisPreparer(BaseObjectPreparer):

    @classmethod
    def _service_enabled_name(cls):
        return consts.REDIS_ENABLED

    @classmethod
    def _get_provider_klass(cls) -> t.Type[BaseObjectProvider]:
        return RedisProvider

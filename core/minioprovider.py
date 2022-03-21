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
import certifi
import os
import urllib3
from datetime import timedelta
from minio import Minio
from common import consts
from common.objpreparer import BaseObjectProvider, BaseObjectPreparer


class BridgeMinio(Minio):

    def __del__(self):
        ...  # we need to keep the pool, dont close it


class MinioProvider(BaseObjectProvider):

    def __init__(self, config=None):
        super(MinioProvider, self).__init__(config=config)
        self._pool: t.Optional[urllib3.PoolManager] = None
        self.address: t.Optional[str] = None
        self.access_key = None
        self.secret_key = None
        self.session_token = None
        self.secure = False
        self.region = None
        self.credentials = None

    def do_configure(self):
        self.address = self.get_config_value(consts.MINIO_ADDRESS, None)
        self.access_key = self.get_config_value(consts.MINIO_ACCESS_KEY, None)
        self.secret_key = self.get_config_value(consts.MINIO_SECRET_KEY, None)
        self.secure = self.get_config_value(consts.MINIO_SECURED, None)
        timeout = timedelta(minutes=5).seconds
        self._pool = urllib3.PoolManager(timeout=urllib3.util.Timeout(connect=timeout, read=timeout),
                                         maxsize=10,
                                         cert_reqs='CERT_REQUIRED',
                                         ca_certs=os.environ.get('SSL_CERT_FILE') or certifi.where(),
                                         retries=urllib3.Retry(
                                             total=5,
                                             backoff_factor=0.2,
                                             status_forcelist=[500, 502, 503, 504])
                                         )

    def do_stop(self):
        self._pool.clear()

    def get_minio(self):
        return BridgeMinio(self.address, access_key=self.access_key, secret_key=self.secret_key,
                           session_token=self.session_token, secure=self.secure, http_client=self._pool)


class MinioPreparer(BaseObjectPreparer):

    @classmethod
    def _service_enabled_name(cls):
        return consts.MINIO_ENABLED

    @classmethod
    def _get_provider_klass(cls) -> t.Type[BaseObjectProvider]:
        return MinioProvider

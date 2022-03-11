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

from core.transadapter import TransportAdapter


class DefaultTransportAdapter(TransportAdapter):
    """Default Transport Adapter"""

    def __init__(self, config=None):
        super(DefaultTransportAdapter, self).__init__(config=config)

    def transform_message(self, obj: object, message: str) -> str:
        """Transform message from outside to be readable by the bridge

        This is the default adapter, by default it just pass received message.
        When require to transform stream message from outside system,
        e.g: celery, or else, create a new class inheriting Transport Adapter,
        and reimplement the transformation on transform_message"""

        return message
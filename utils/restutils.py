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

import asyncio
import logging
import functools
from threading import RLock

_IS_RUNNING = False
_LOCK = RLock()


def message(status, message_str: str):
    response_object = {"status": status, "message": message_str}
    return response_object


def validation_error(status, errors):
    response_object = {"status": status, "errors": errors}

    return response_object


def err_resp(msg, reason, code):
    err = message(False, msg)
    err["error_reason"] = reason
    return err, code


def internal_err_resp():
    err = message(False, "Error occurs during the process!")
    err["error_reason"] = "server_error"
    return err, 500


def execute_async(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner


def _get_klass_module(class_name):
    components = class_name.split(".")
    return components, ".".join(components[:-1])


def get_klass(class_name):
    mod = None
    components, import_modules = _get_klass_module(class_name)
    try:
        mod = __import__(import_modules)
        for cmp in components[1:]:
            mod = getattr(mod, cmp)
    except Exception as ex:
        logging.error(ex)
    return mod


def is_running() -> bool:
    return _IS_RUNNING


def set_stopped(value: bool) -> None:
    global _IS_RUNNING
    global _LOCK
    _LOCK.acquire(blocking=True)
    try:
        _IS_RUNNING = not value
    finally:
        _LOCK.release()

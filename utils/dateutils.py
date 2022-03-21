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
import datetime as dt


def datetime_to_integer(dttm: dt.datetime):
    return 10000000000 * dttm.year + 100000000 * dttm.month + 1000000 * dttm.day + \
           10000 * dttm.hour + 100 * dttm.minute + dttm.second


def date_to_integer(dt: dt.date):
    return 10000 * dt.year + 100 * dt.month + dt.day


def time_to_integer(tm: dt.time):
    return 10000 * tm.hour + 100 * tm.minute + tm.second


def datetime_from_integer(n):
    nlong = int(n)
    s  = int(nlong % 100)
    m  = int(nlong / 100) % 100
    h  = int(nlong / 10000) % 100
    dd = int(nlong / 1000000) % 100
    mm = int(nlong / 100000000) % 100
    yy = int(nlong / 10000000000)
    return dt.datetime(yy, mm, dd, h, m, s)


def date_from_integer(n):
    nint = int(n)
    d = int(nint % 100)
    m = int(nint / 100) % 100
    y = int(nint / 10000)
    return dt.date(y, m, d)


def time_from_integer(n):
    nint = int(n)
    h = int(nint % 100)
    m = int(nint / 100) % 100
    s = int(nint / 10000)
    return dt.time(h, m, s)

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

import logging

SHUTDOWN_ADDR = "shutdown.addr"
SHUTDOWN_PORT = "shutdown.port"

LOG_LEVEL = "log.level"
LOG_FORMAT = "log.format"
LOG_FILE = "log.file"

LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "WARNING"
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_CRITICAL = "CRITICAL"

log_level = {LOG_LEVEL_INFO: logging.INFO,
             LOG_LEVEL_WARNING: logging.WARNING,
             LOG_LEVEL_DEBUG: logging.DEBUG,
             LOG_LEVEL_ERROR: logging.ERROR,
             LOG_LEVEL_CRITICAL: logging.CRITICAL}

DEFAULT_LOG_FORMAT = "%(asctime)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILE = "./log/ibridge.log"
DEFAULT_LOGF_LEVEL = log_level[LOG_LEVEL_INFO]

DEFAULT_SHUTDOWN_ADDR = "127.0.0.1"
DEFAULT_SHUTDOWN_PORT = 9999

MQ_TRANSPORT_COUNT = "mq.transport.count"
MQ_TRANSPORT_TYPE = "mq.transport.{0}.type"
MQ_TRANSPORT_ADDR = "mq.transport.{0}.address"
MQ_TRANSPORT_PORT = "mq.transport.{0}.port"
MQ_TRANSPORT_USER = "mq.transport.{0}.user"
MQ_TRANSPORT_PASS = "mq.transport.{0}.passwd"
MQ_TRANSPORT_CHANNEL = "mq.transport.{0}.channel"

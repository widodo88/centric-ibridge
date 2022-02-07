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

import os
import re
import sys
import uvicorn
import logging
from common import consts
from fastapi import FastAPI
from dotenv import dotenv_values
from starlette.staticfiles import StaticFiles
from logging.handlers import TimedRotatingFileHandler


def do_configure():
    config = dotenv_values(".env")
    mode = "false" if consts.PRODUCTION_MODE not in config else config[consts.PRODUCTION_MODE]
    mode = "false" if mode is None else mode
    consts.IS_PRODUCTION_MODE = mode.lower() == "true"
    consts.DEFAULT_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    return config


def configure_logging(config):
    default_level = consts.log_level[config[consts.LOG_LEVEL]] if consts.LOG_LEVEL in config \
        else consts.DEFAULT_LOG_LEVEL
    log_format = config[consts.LOG_FORMAT] if consts.LOG_FORMAT in config else consts.DEFAULT_LOG_FORMAT
    log_date_format = consts.DEFAULT_LOG_DATE_FORMAT
    log_file = config[consts.RESTAPI_LOG_FILE] if consts.RESTAPI_LOG_FILE in config else consts.DEFAULT_RESTAPI_LOG_FILE
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=5)
    logging.basicConfig(format=log_format, datefmt=log_date_format, handlers=[handler], level=default_level)


def create_app():
    config = do_configure()
    configure_logging(config)
    fast_app = FastAPI()
    fast_app.mount("/static", StaticFiles(directory=os.path.join(consts.DEFAULT_SCRIPT_PATH, "resources/static")),
                   name="static")
    return fast_app


app = create_app()

if __name__ == '__main__':
    is_debug = not consts.IS_PRODUCTION_MODE
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(uvicorn.run("irest:app", debug=is_debug, reload=True))

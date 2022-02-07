#
# Copyright (c) 2019 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#

import configparser
from common import consts

module_config = None


def get_configuration():
    """
    Read configuration properties
    :return:
    """
    global module_config
    if module_config is not None:
        return module_config

    config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.MODULE_CONFIG_FILE)
    module_config = configparser.ConfigParser()
    module_config.read(config_file)

    return module_config


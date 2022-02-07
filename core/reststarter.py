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
from utils import restutils
from core.baseappsrv import BaseAppServer


class RESTServerStarter(BaseAppServer):

    def __init__(self, config=None, standalone: bool = True):
        super(RESTServerStarter, self).__init__(config=config, standalone=standalone)

    def do_configure(self):
        super(RESTServerStarter, self).do_configure()
        
    def do_start(self):
        restutils.set_stopped(False)
        super(RESTServerStarter, self).do_start()

    def do_stop(self):
        restutils.set_stopped(True)
        super(RESTServerStarter, self).do_stop()

    def handle_stop_event(self, obj):
        self.stop()
        logging.info("Shutting down REST Service")

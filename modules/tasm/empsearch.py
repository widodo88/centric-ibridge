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

import traceback
import logging
from core.prochandler import CommandProcessor
from core.msgobject import mq_event
from utils.krclient import KRWebClient
from solr.core import SolrConnection


class HREmpUpdateSearchDB(CommandProcessor):

    def __init__(self):
        super(HREmpUpdateSearchDB, self).__init__()
        prop = self.get_module_configuration()
        self._module = 'TASM@EMPSEARCHDB'
        self._props = prop[self._module] if self._module in prop else dict()
        self._rest_service = None
        self._solr_connection = None

    def do_configure(self):
        try:
            if self._rest_service is None:
                self._rest_service = KRWebClient(parent=self.get_parent())
                self._rest_service.set_user(self._props['KR_REST_USERNAME'], self._props['KR_REST_PASSWORD'])
            if self._solr_connection is None:
                self._solr_connection = SolrConnection("{0}/{1}".format(self._props['SOLR_URL'],
                                                                        self._props['SOLR_EMP_NAMESPACE']))
        except Exception:
            logging.error(traceback.format_exc())

    def get_employee_info(self, cono, emid):
        module = self._rest_service.create_module(self._props['BASE_MODULE'])
        command = module.create_command('getEmpSearchableInfo')
        result = command.get(cono=cono, emid=emid)
        return result.json()

    def delete_search_db_record(self, info):
        if not self._solr_connection:
            return
        self._solr_connection.delete(id=info['id'])
        self._solr_connection.commit()

    def update_search_db_record(self, info):
        if not self._solr_connection:
            return
        self._solr_connection.add(**info)
        self._solr_connection.commit()

    @mq_event
    def update_emp_search_db(self, cono=None, emid=None):
        if (not cono) or (not emid):
            logging.error("Not enough parameter to process update_emp_search_db")
            return
        logging.info("Processing Update Search for EMID: {0}".format(emid))
        try:
            info = self.get_employee_info(cono, emid)
            if 'id' not in info:
                return
            self.delete_search_db_record(info)
            self.update_search_db_record(info)
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            logging.info("End Update Search for EMID: {0}".format(emid))

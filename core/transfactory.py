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

from common import consts
from core.objfactory import AbstractFactory


class TransportFactory(AbstractFactory):

    def __init__(self, config):
        super(TransportFactory, self).__init__(config)
        self.dictionary = {}

    def do_configure(self):
        keys = [key for key in consts.TRANSPORT_INFO if key not in self.dictionary]
        self.dictionary.update([(key, self.import_klass(consts.TRANSPORT_INFO[key])) for key in keys])

    def create_object(self, name, **kwargs):
        if name not in self.dictionary:
            return None
        klass = self.dictionary[name]
        index = kwargs.pop("index", 0)
        config = self.get_configuration()
        instance = self.create_instance(klass)
        instance.set_configuration(config)
        instance.set_transport_index(index)
        return instance


class TransportPreparer(object):

    @classmethod
    def get_config_value(cls, config, key, index, default):
        fmtkey = key.format(index)
        return config[fmtkey] if fmtkey in config else default

    @classmethod
    def prepare_transports(cls, config, listener, container):
        factory = TransportFactory(config)
        factory.do_configure()
        trans_count = config[consts.MQ_TRANSPORT_COUNT] if consts.MQ_TRANSPORT_COUNT in config else -1
        trans_count = int(trans_count)
        if trans_count <= 0:
            return
        for index in range(trans_count):
            mqtype = cls.get_config_value(config, consts.MQ_TRANSPORT_TYPE, index, None)
            if mqtype:
                instance = factory.create_object(mqtype, index=index)
                if instance:
                    instance.add_listener(listener)
                    container.add_object(instance)








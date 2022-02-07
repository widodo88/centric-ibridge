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

import amqp
import logging
from common import consts
from core.transhandler import TransportHandler


class AmqpTransport(TransportHandler):
    def __init__(self, config=None, transport_index=0):
        super(AmqpTransport, self).__init__(config=config, transport_index=transport_index)
        self.amqp_config = None
        self.host = None
        self.durable = True
        self.auto_delete = False
        # fanout, direct, topic
        self.type = "direct"
        self._my_exchange = None

    def do_configure(self):
        super(AmqpTransport, self).do_configure()
        self._my_exchange = self._get_config_value(consts.MQ_MY_EXCHANGE, None)
        self.host = "{0}:{1}".format(self.get_transport_address(), self.get_transport_port())
        self.amqp_config = amqp.Connection(host=self.host, userid=self.get_transport_user(),
                                           password=self.get_transport_password())

    def do_listen(self):
        client = self.amqp_config.channel(self.get_transport_channel())
        client.queue_declare(queue=self.get_transport_client_id(), durable=self.durable, auto_delete=self.auto_delete)
        client.exchange_declare(exchange=self.get_client_exchange(), type=self.type, durable=self.durable,
                                auto_delete=self.auto_delete)
        client.queue_bind(queue=self.get_transport_client_id(), exchange=self.get_client_exchange())
        client.basic_consume(queue=self.get_transport_client_id(), no_ack=True, callback=self.handle_message)

        try:
            try:
                while self.is_running():
                    client.wait()
                client.close()
            except Exception as ex:
                logging.error(ex)
                client.close()
                raise
        finally:
            self.amqp_config.close()

    def get_client_exchange(self):
        return self._my_exchange

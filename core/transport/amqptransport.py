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
import logging
from core.transhandler import TransportHandler
from amqplib import client_0_8 as amqp


class amqpTransport(TransportHandler):
    def __init__(self):
        self.amqp_config = None
        self.host = None
        self.durable = True
        self.auto_delete = False
        # fanout, direct, topic
        self.type = "direct"
        super(amqpTransport, self).__init__()

    def do_configure(self):
        super(amqpTransport, self).do_configure()
        if not self.amqp_config:
            self.host = "{0}:{1}".format(self.get_transport_address(), self.get_transport_port())
            self.amqp_config = amqp.Connection(host=self.host, userid=self.get_transport_user(),
                                               password=self.get_transport_password())

    def do_listen(self):
        client = self.amqp_config.channel(self.get_transport_channel())
        client.queue_declare(queue=self.get_transport_clientid(), durable=self.durable, auto_delete=self.auto_delete)
        client.exchange_declare(exchange=self.get_client_exchange(), type=self.type, durable=self.durable,
                                auto_delete=self.auto_delete)
        client.queue_bind(queue=self.get_transport_clientid(), exchange=self.get_client_exchange())
        client.basic_consume(queue=self.get_transport_clientid(), no_ack=True, callback=self.handle_message)

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

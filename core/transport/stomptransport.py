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

from core.transhandler import TransportHandler
from stompest.config import StompConfig
from stompest.protocol.spec import StompSpec
from stompest.sync import Stomp
import logging
import time


class StompTransport(TransportHandler):

    def __init__(self):
        super(StompTransport, self).__init__()
        self._stomp_config = None
        self._target_clientid = None
        self._client_heartbeat = None

    def do_configure(self):
        super(StompTransport, self).do_configure()
        self._target_clientid = self._get_config_value(consts.MQ_TRANSPORT_CLIENTID, None)
        self._client_heartbeat = self._get_config_value(consts.MQ_CLIENT_HEARTBEAT, 20000)
        if not self._stomp_config:
            self._stomp_config = StompConfig("tcp://{0}:{1}".format(self.get_transport_address(),
                                                                    self.get_transport_port()),
                                             login=self.get_transport_user(),
                                             passcode=self.get_transport_password(),
                                             version=StompSpec.VERSION_1_2)

    def do_listen(self):
        client = Stomp(self.stomp_config)
        logging.info("Subscribing {} on channel {}".format(self.get_transport_address(), self.get_transport_channel()))
        client.connect(versions=[StompSpec.VERSION_1_2], heartBeats=(self.get_client_heartbeat(),
                                                                     self.get_client_heartbeat()))
        client_heartbeat = client.clientHeartBeat / 1000.0
        token = client.subscribe(self.get_transport_channel(), {StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
                                                                StompSpec.ID_HEADER: self.get_transport_clientid()})
        try:
            try:
                while True:
                    if client.canRead(2):
                        frame = client.receiveFrame()
                        cmd_str = frame.body
                        client.ack(frame)
                        if cmd_str is not None:
                            self.handle_message(cmd_str)
                        else:
                            logging.info("Message is Empty, bypassing")
                    else:
                        time.sleep(0.4)
                    if (time.time() - client.lastSent) > client_heartbeat:
                        client.beat()
                    if not self.is_running():
                        client.unsubscribe(token)
                        break
            except Exception as ex:
                logging.error(ex)
                client.unsubscribe(token)
                raise
        finally:
            client.disconnect()

    def get_transport_clientid(self):
        return self._target_clientid

    def get_client_heartbeat(self):
        return self._client_heartbeat

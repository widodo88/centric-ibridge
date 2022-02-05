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

import argparse
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from dotenv import dotenv_values
from common import consts
from core.startable import Startable
from core.bridgesrv import BridgeServer
from core.msgobject import MessageEvent, MessageCommand


class StoreDictKeyPair(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        _dict = dict()
        for kv in values:
            k, v = kv.split("=")
            _dict[k] = v
        setattr(namespace, self.dest, _dict)


class BridgeApp(Startable):

    def __init__(self):
        super(BridgeApp, self).__init__()
        self.parser = argparse.ArgumentParser(prog='ibridge', description='Integration Bridge Server v3.0')

    def do_configure(self):
        sub_parser = self.parser.add_subparsers()
        sub_parser.add_parser('start', help='Start %(prog)s daemon').set_defaults(func=self.do_start_command)
        sub_parser.add_parser('stop', help='Stop %(prog)s daemon').set_defaults(func=self.do_stop_command)
        sub_parser.add_parser('altstop', help='Stop %(prog)s daemon in alternate way')\
            .set_defaults(func=self.do_alt_stop_command)

        notify_parser = sub_parser.add_parser('notify', help='Send notification to %(prog)s daemon')
        notify_parser.add_argument('event', help='Event in format MODULE@SUBMODULE:EVENT_NAME')
        notify_parser.add_argument('-a', '--args', help='List of parameter required', nargs="+", dest="args",
                                   metavar="val1 ")
        notify_parser.add_argument('-k', '--kwargs', help='List of parameter required', nargs="+", dest="kwargs",
                                   action=StoreDictKeyPair, metavar="key1=val1")
        notify_parser.set_defaults(func=self.do_send_notification)

        command_parser = sub_parser.add_parser('command', help='Send command to %(prog)s daemon')
        command_parser.add_argument('command', help='Command in format MODULE@SUBMODULE:proc_name')
        command_parser.add_argument('-a', '--args', help='List of parameter required', nargs="+", dest="args",
                                   metavar="val1 ")
        command_parser.add_argument('-k', '--kwargs', help='List of parameter required', nargs="+", dest="kwargs",
                                   action=StoreDictKeyPair, metavar="key1=val1")
        command_parser.set_defaults(func=self.do_send_command)

    def do_start(self):
        self.evaluate_args(self.parser.parse_args())

    def evaluate_args(self, args):
        if hasattr(args, 'func'):
            print("\n" + self.parser.description + "\n")
            args.func(args)
        else:
            self.parser.print_help()

    def do_start_command(self, args):
        logging.info(self.parser.description)
        print("Starting server", end=" ...")
        bridgesrv = BridgeServer.get_default_instance()
        bridgesrv.set_configuration(self.get_configuration())
        bridgesrv.start()
        print("Done")
        bridgesrv.join()

    def do_stop_command(self, args):
        print("Stopping ", end=" ...")
        bridgesrv = BridgeServer.get_default_instance()
        bridgesrv.set_configuration(self.get_configuration())
        try:
            bridgesrv.send_shutdown_signal()
            print("Done")
        except Exception as ex:
            print("Unable to shutdown \n\nReason: {0}".format(ex))

    def do_alt_stop_command(self, args):
        print("Stopping ", end=" ...")
        bridgesrv = BridgeServer.get_default_instance()
        bridgesrv.set_configuration(self.get_configuration())
        try:
            bridgesrv.alt_shutdown_signal()
            print("Done")
        except Exception as ex:
            print("Unable to shutdown \n\nReason: {0}".format(ex))

    def do_send_notification(self, args):
        print("Notifying ", end=" ...")
        data, event = args.event.split(":")
        module, submodule = data.split("@")
        arg = args.args
        kwarg = args.kwargs
        arg = arg if arg else []
        kwarg = kwarg if kwarg else {}
        message_object = MessageEvent()
        message_object.set_event(module, submodule, event)
        message_object.set_parameters(*arg, **kwarg)
        bridgesrv = BridgeServer.get_default_instance()
        bridgesrv.set_configuration(self.get_configuration())
        try:
            bridgesrv.notify_server(message_object)
            print("Done")
        except Exception as ex:
            print("Unable to send notification \n\nReason: {0}".format(ex))

    def do_send_command(self, args):
        print("Sending command ", end=" ...")
        data, event = args.event.split(":")
        module, submodule = data.split("@")
        arg = args.args
        kwarg = args.kwargs
        arg = arg if arg else []
        kwarg = kwarg if kwarg else {}
        message_object = MessageCommand()
        message_object.set_command(module, submodule, event)
        message_object.set_parameters(*arg, **kwarg)
        bridgesrv = BridgeServer.get_default_instance()
        bridgesrv.set_configuration(self.get_configuration())
        try:
            bridgesrv.notify_server(message_object)
            print("Done")
        except Exception as ex:
            print("Unable to send notification \n\nReason: {0}".format(ex))


def configure_logging(config):
    default_level = consts.log_level[config[consts.LOG_LEVEL]] if consts.LOG_LEVEL in config \
        else consts.DEFAULT_LOGF_LEVEL
    log_format = config[consts.LOG_FORMAT] if consts.LOG_FORMAT in config else consts.DEFAULT_LOG_FORMAT
    log_date_format = consts.DEFAULT_LOG_DATE_FORMAT
    log_file = config[consts.LOG_FILE] if consts.LOG_FILE in config else consts.DEFAULT_LOG_FILE
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=5)
    logging.basicConfig(format=log_format, datefmt=log_date_format, handlers=[handler], level=default_level)


if __name__ == '__main__':
    prev_sys_argv = sys.argv[:]
    config = dotenv_values(".env")
    configure_logging(config)
    main_app = BridgeApp()
    main_app.set_configuration(config)
    main_app.start()

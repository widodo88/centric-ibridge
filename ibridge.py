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

import argparse
import logging
import sys
import os
import re
from logging.handlers import TimedRotatingFileHandler
from dotenv import dotenv_values
from multiprocessing_logging import install_mp_handler
from common import consts
from common.objloader import ObjectLoader
from core.baseappsrv import BaseAppServer
from core.shutdn import ShutdownHookMonitor
from common.msgobject import MessageEvent, MessageCommand


class StoreDictKeyPair(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        _dict = dict()
        for kv in values:
            k, v = kv.split("=")
            _dict[k] = v
        setattr(namespace, self.dest, _dict)


class BridgeApp(BaseAppServer, ObjectLoader):

    def __init__(self):
        super(BridgeApp, self).__init__()
        self.parser = argparse.ArgumentParser(prog='ibridge', description='Integration Bridge Server v3.0')

    def do_configure(self):
        self.service_enabled = False
        self.parse_config()
        self.set_transport_listener(self.create_transport_listener())

        sub_parser = self.parser.add_subparsers()
        sub_parser.add_parser('start', help='Start %(prog)s daemon').set_defaults(func=self.do_start_command)
        sub_parser.add_parser('stop', help='Stop %(prog)s daemon').set_defaults(func=self.do_stop_command)
        sub_parser.add_parser('altstop', help='Stop %(prog)s daemon in alternate way') \
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
        super(BridgeApp, self).do_configure()
        self.evaluate_args(self.parser.parse_args())

    def evaluate_args(self, args):
        if hasattr(args, 'func'):
            print("\n" + self.parser.description + "\n")
            args.func(args)
        else:
            self.parser.print_help()

    def configure_shutdown_monitor(self):
        config = self.get_configuration()
        shutdown_hook = ShutdownHookMonitor.get_default_instance()
        shutdown_hook.set_configuration(config)
        shutdown_hook.add_listener(self.get_transport_listener())
        return shutdown_hook

    def configure_app_server(self, app_server_klass_name, standalone=False):
        app_server_klass = self._get_klass(app_server_klass_name)
        if not issubclass(app_server_klass, BaseAppServer):
            return
        server_instance = app_server_klass.get_default_instance()
        server_instance.set_configuration(self.get_configuration())
        server_instance.standalone = standalone
        return server_instance

    def configure_services(self):
        self.add_object(self.configure_shutdown_monitor())
        service_enabled = [service for service in consts.SERVICES_AVAILABLE if service[1]]
        for service in service_enabled:
            server_instance = self.configure_app_server(service[0])
            self.add_object(server_instance) if server_instance else None

    def do_start_command(self, args):
        print("Starting", end=" ... ")
        logging.info(self.parser.description)
        self.service_enabled = True
        self.configure_services()

    def do_stop_command(self, args):
        print("Stopping ", end=" ... ")
        self.send_shutdown_signal()

    def do_alt_stop_command(self, args):
        app_server_klass = self._get_klass(consts.BRIDGE_SERVICE)
        if not issubclass(app_server_klass, BaseAppServer):
            return
        print("Stopping ", end=" ... ")
        bridge_server = app_server_klass.get_default_instance()
        bridge_server.set_configuration(self.get_configuration())
        bridge_server.alt_shutdown_signal()

    def do_send_notification(self, args):
        print("Notifying ", end=" ...")
        data, event = args.event.split(":")
        module, submodule = data.split("@")
        arg = args.args
        kwarg = args.kwargs
        arg = arg if arg else []
        kwarg = kwarg if kwarg else {}
        message_object = MessageEvent.create_message(module, submodule, event, *arg, **kwarg)
        appserver_klass = self._get_klass(consts.BRIDGE_SERVICE)
        bridge_server = appserver_klass.get_default_instance()
        bridge_server.set_configuration(self.get_configuration())
        bridge_server.notify_server(message_object)

    def do_send_command(self, args):
        print("Sending command ", end=" ...")
        data, command = args.command.split(":")
        module, submodule = data.split("@")
        arg = args.args
        kwarg = args.kwargs
        arg = arg if arg else []
        kwarg = kwarg if kwarg else {}
        message_object = MessageCommand.create_message(module, submodule, command, *arg, **kwarg)
        appserver_klass = self._get_klass(consts.BRIDGE_SERVICE)
        bridge_server = appserver_klass.get_default_instance()
        bridge_server.set_configuration(self.get_configuration())
        bridge_server.notify_server(message_object)

    def send_shutdown_signal(self):
        try:
            shutdown_monitor = self.configure_shutdown_monitor()
            shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
            shutdown_monitor.send_shutdown_signal() if shutdown_monitor else None
        except Exception as ex:
            print("Unable to connect to server")

    def parse_config(self):
        config = self.get_configuration()
        bridge_enabled = config[consts.BRIDGE_ENABLED] if consts.BRIDGE_ENABLED in config else "false"
        restapi_enabled = config[consts.RESTAPI_ENABLED] if consts.RESTAPI_ENABLED in config else "false"
        bridge_enabled = "false" if bridge_enabled is None else bridge_enabled
        restapi_enabled = "false" if restapi_enabled is None else restapi_enabled
        consts.SERVICES_AVAILABLE[0][1] = bridge_enabled.lower() == "true"
        consts.SERVICES_AVAILABLE[1][1] = restapi_enabled.lower() == "true"

    def _verify_klass(self, klass, class_name):
        return klass if issubclass(klass, BaseAppServer) else None

    def handle_stop_event(self, obj):
        self.stop()
        logging.info("Shutting down")

    def join(self):
        shutdown_monitor = self.get_object(ShutdownHookMonitor)
        shutdown_monitor = ShutdownHookMonitor.get_default_instance() if not shutdown_monitor else shutdown_monitor
        shutdown_monitor.join() if shutdown_monitor else None

    def listen(self):
        self.join() if self.service_enabled else None


def configure_logging(config):
    default_level = consts.log_level[config[consts.LOG_LEVEL]] if consts.LOG_LEVEL in config \
        else consts.DEFAULT_LOG_LEVEL
    log_format = config[consts.LOG_FORMAT] if consts.LOG_FORMAT in config else consts.DEFAULT_LOG_FORMAT
    log_date_format = consts.DEFAULT_LOG_DATE_FORMAT
    log_file = config[consts.LOG_FILE] if consts.LOG_FILE in config else consts.DEFAULT_LOG_FILE
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    handler = TimedRotatingFileHandler(log_file, when='midnight', backupCount=5)
    logging.basicConfig(format=log_format, datefmt=log_date_format, handlers=[handler], level=default_level)
    install_mp_handler()


def main(argv=None):
    if argv:
        assert isinstance(argv, list)
        sys.argv = argv
    consts.DEFAULT_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    consts.prepare_path()
    config = dotenv_values("{0}/.env".format(consts.DEFAULT_SCRIPT_PATH))
    configure_logging(config)
    try:
        main_app = BridgeApp()
        main_app.set_configuration(config)
        main_app.start()
        print("Done")
        main_app.listen() if main_app.is_enabled() else None
    except Exception as ex:
        print("Unable to send notification \n\nReason: {0}".format(ex))


if __name__ == '__main__':
    consts.DEFAULT_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(main())

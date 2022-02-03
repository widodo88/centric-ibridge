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
from common import consts
from core.startable import Startable, StartableManager
from core.commandproc import MessageFactory, MessageEvent, MessageCommand
from multiprocessing.pool import ThreadPool
from configparser import ConfigParser
from jproperties import Properties
from threading import get_ident


class BaseExecutor(Startable):

    def __init__(self, config=None, module=None, workers=4):
        super(BaseExecutor, self).__init__(config)
        self._max_processes = workers
        self._pool = None
        self._module = module
        self._props = None

    def do_configure(self):
        self._max_processes = self._max_processes if self._max_processes > 0 else 4

    def do_start(self):
        self._pool = ThreadPool(processes=self._max_processes)

    def do_stop(self):
        self._pool.terminate()

    def get_module(self):
        return self._module

    def is_valid_module(self, message_obj):
        return message_obj.MODULE == self._module

    def get_properties(self):
        return self._props

    def set_properties(self, props):
        self._props = props

    def execute_module(self, message_obj):
        pass


class EventExecutor(BaseExecutor):

    def __init__(self, config=None, module=None, workers=4):
        super(EventExecutor, self).__init__(config, module, workers)
        self.modules = dict()

    def is_valid_module(self, message_obj):
        return super(EventExecutor, self).is_valid_module(message_obj) and isinstance(message_obj, MessageEvent)

    def execute_module(self, message_obj):
        # TODO: perform task execution here
        pass

    def assign_event(self, module, func, event):
        logging.info(
            "Submitting event {0}.{1}:{2} params: {3}".format(event.MODULE, event.SUBMODULE,
                                                              event.EVENT, event.PARAMS))
        self._pool.apply_async(self.do_execute_event(module, func, event))

    @staticmethod
    def do_execute_event(module, func, event):
        try:
            logging.info("Processing {0} event on thread {1}".format(event.get_module_id(), get_ident()))
            module.perform_notify(func, event)
        except Exception as e:
            logging.error(e)
        finally:
            logging.info("End processing {0} event on thread {1}".format(event._get_module_id(), get_ident()))


class CommandExecutor(BaseExecutor):

    def __init__(self, config=None, module=None, workers=4):
        super(CommandExecutor, self).__init__(config, module, workers)
        self.modules = dict()

    def is_valid_module(self, message_obj):
        return super(CommandExecutor, self).is_valid_module(message_obj) and isinstance(message_obj, MessageCommand)

    def execute_module(self, message_obj):
        # TODO: perform task execution here
        pass

    def assign_task(self, module, command):
        logging.info(
            "Submitting command {0}.{1}:{2} params: {3}".format(command.MODULE, command.SUBMODULE,
                                                                command.COMMAND, command.PARAMS))
        self._pool.apply_async(self.do_execute, (module, command))

    @staticmethod
    def do_execute(module, command):
        try:
            logging.info("Processing {0} command on thread {1}".format(command.get_module_id(), get_ident()))
            module.perform_exec(command)
        except Exception as e:
            logging.error(e)
        finally:
            logging.info("End processing {0} command on thread {1}".format(command.get_module_id(), get_ident()))


class ExecutorFactory(object):

    def __init__(self):
        self._command_props = None
        self._event_props = None
        self._configured = False

    def do_configure(self):
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_COMMAND_FILE)
        self._command_props = Properties()
        with open(config_file, "rb") as file_prop:
            self._command_props.load(file_prop, "utf-8")
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_EVENT_FILE)
        self._event_props = ConfigParser()
        self._event_props.read(config_file)

    def generate(self, config, message_obj):
        module_obj = None
        if not self._configured:
            self.do_configure()
        if isinstance(message_obj, MessageEvent):
            module_obj = EventExecutor(config, message_obj.MODULE)
            module_obj.set_properties(self._event_props)
        elif isinstance(message_obj, MessageCommand):
            module_obj = CommandExecutor(config, message_obj.MODULE)
            module_obj.set_properties(self._command_props)
        return module_obj


class BaseExecutionManager(StartableManager):

    def __init__(self, config):
        super(BaseExecutionManager, self).__init__(config)
        self._executor_factory = ExecutorFactory()

    def register_listener(self, listener):
        listener.set_on_message_received(self.on_handle_message)

    def get_valid_module(self, message_obj):
        object_list = [obj for obj in self.get_objects() if isinstance(obj, BaseExecutor)]
        for module_obj in object_list:
            if module_obj.is_valid_module(message_obj):
                return module_obj
        return None

    def on_handle_message(self, obj, message):
        message_object = MessageFactory.generate(message) if message else None
        if (not message_object) or (not self.is_running()):
            logging.error("Could not parse message correctly: {0}".format(message))
            return
        module_object = self.get_valid_module(message_object)
        module_object = module_object if module_object else self._register_module_object(message_object)
        if module_object:
            module_object.execute_module(message_object)

    def _register_module_object(self, message_obj):
        module_object = self._executor_factory.generate(self.get_configuration(), message_obj)
        self.add_object(module_object if module_object else None)
        return module_object




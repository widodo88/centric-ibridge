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
from common import consts
from core.objfactory import AbstractFactory
from core.startable import Startable, StartableManager
from core.msgobject import MessageFactory, MessageEvent, MessageCommand
from core.msghandler import MessageNotifier
from core.prochandler import CommandProcessor
from multiprocessing.pool import ThreadPool
from configparser import ConfigParser
from jproperties import Properties
from threading import get_ident


class DummyClass(object):
    pass


class BaseExecutor(Startable):

    def __init__(self, config=None, module=None, workers=4):
        super(BaseExecutor, self).__init__(config=config)
        self._collection = dict()
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

    def _get_klass_from_cache(self, class_name):
        return None

    def _register_klass_to_cache(self, class_name, mod):
        return None

    def _get_klass_module(self, msg_obj):
        class_name = msg_obj if isinstance(msg_obj, str) \
            else self._props.properties[msg_obj.get_module_id()]
        components = class_name.split(".")
        return components, ".".join(components[:-1]), class_name

    def _get_klass(self, msg_obj):
        components, import_modules, class_name = self._get_klass_module(msg_obj)
        logging.debug("BaseExecutor.get_klass: {0} output {1} - {2}".format(msg_obj, components, import_modules))
        mod = self._get_klass_from_cache(class_name)
        if not mod:
            try:
                mod = __import__(import_modules)
                for cmp in components[1:]:
                    mod = getattr(mod, cmp)
                mod = mod if issubclass(mod, CommandProcessor) else None
                if mod:
                    self._register_klass_to_cache(class_name, mod)
            except Exception as ex:
                logging.error(ex)
        return mod

    def _create_object(self, klass):
        if not klass:
            return None
        if klass.__name__ not in self._collection:
            self._collection[klass.__name__] = DummyClass()
        parent = self._collection[klass.__name__]
        module = object.__new__(klass)
        module.__init__()
        module.set_parent(parent)
        module.do_configure()
        logging.debug("BaseExecutor.create_object: {0} output {1}".format(klass, module))
        return module


class ModuleExecutor(BaseExecutor):
    def __init__(self, config=None, module=None, workers=4):
        super(ModuleExecutor, self).__init__(config=config, module=module, workers=workers)
        self._module_dict = dict()

    def _get_klass_from_cache(self, class_name):
        return self._module_dict[class_name] if class_name in self._module_dict else None

    def _register_klass_to_cache(self, class_name, mod):
        self._module_dict[class_name] = mod

    def has_service(self, message_obj):
        return None


class EventExecutor(ModuleExecutor):

    def __init__(self, config=None, module=None, workers=4):
        super(EventExecutor, self).__init__(config=config, module=module, workers=workers)

    def is_valid_module(self, message_obj):
        return super(EventExecutor, self).is_valid_module(message_obj) and isinstance(message_obj, MessageEvent)

    def has_service(self, message_obj):
        props = self.get_properties()
        return props.has_section(message_obj.get_module_id())

    def execute_module(self, message_obj):
        if self.has_service(message_obj):
            try:
                props = self.get_properties()
                section_props = props[message_obj.get_module_id()]
                str_mod = None if message_obj.EVENT not in section_props else section_props[message_obj.EVENT]
                list_mod = [str_item.split(":") for str_item in (str_mod.split(",") if str_mod else [])]
                for str_mod, str_func in list_mod:
                    klass = self._get_klass(str_mod)
                    module = self._create_object(klass)
                    logging.debug("EventExecutor.execute_module: klass and module {0} - {1}".format(klass, module))
                    self.assign_event(module, str_func, message_obj)
            except Exception as ex:
                logging.error(ex)
        else:
            logging.error("Could not parse message correctly")

    def assign_event(self, module, func, event):
        logging.info("Submitting event {0}.{1}:{2} params: {3}".format(event.MODULE, event.SUBMODULE,
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
            logging.info("End processing {0} event on thread {1}".format(event.get_module_id(), get_ident()))


class CommandExecutor(ModuleExecutor):

    def __init__(self, config=None, module=None, workers=4):
        super(CommandExecutor, self).__init__(config=config, module=module, workers=workers)

    def is_valid_module(self, message_obj):
        return super(CommandExecutor, self).is_valid_module(message_obj) and isinstance(message_obj, MessageCommand)

    def has_service(self, message_obj):
        props = self.get_properties()
        return message_obj.get_module_id() in props.keys()

    def execute_module(self, message_obj):
        if self.has_service(message_obj):
            try:
                klass = self._get_klass(message_obj)
                module = self._create_object(klass)
                logging.debug("CommandExecutor.execute_module: klass and module {0} - {1}".format(klass, module))
                self.assign_task(module, message_obj)
            except Exception as ex:
                logging.error(ex)
        else:
            logging.error("Could not find service for {0}.{1}".format(msgObj.MODULE, msgObj.SUBMODULE))

    def assign_task(self, module, command):
        logging.info("Submitting command {0}.{1}:{2} params: {3}".format(command.MODULE, command.SUBMODULE,
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


class ExecutorFactory(AbstractFactory):

    def __init__(self, config=None):
        super(ExecutorFactory, self).__init__(config=config)
        self._command_props = None
        self._event_props = None
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
        self._configured = True

    def generate(self, config, message_obj):
        module_obj = None
        if not self._configured:
            self.do_configure()
        if isinstance(message_obj, MessageEvent):
            module_obj = EventExecutor(config=config, module=message_obj.MODULE)
            module_obj.set_properties(self._event_props)
        elif isinstance(message_obj, MessageCommand):
            module_obj = CommandExecutor(config=config, module=message_obj.MODULE)
            module_obj.set_properties(self._command_props)
        return module_obj


class BaseExecutionManager(StartableManager):

    def __init__(self, config):
        super(BaseExecutionManager, self).__init__(config=config)
        self._executor_factory = ExecutorFactory(config=config)

    def get_valid_module(self, message_obj):
        object_list = [obj for obj in self.get_objects() if isinstance(obj, BaseExecutor)]
        for module_obj in object_list:
            if module_obj.is_valid_module(message_obj):
                return module_obj
        return None

    def _register_module_object(self, message_obj):
        module_object = self._executor_factory.generate(self.get_configuration(), message_obj)
        self.add_object(module_object if module_object else None)
        return module_object


class MessageExecutionManager(BaseExecutionManager):

    def __init__(self, config):
        super(MessageExecutionManager, self).__init__(config=config)

    def register_listener(self, listener):
        if isinstance(listener, MessageNotifier):
            listener.set_on_message_received(self.on_handle_message)

    def on_handle_message(self, obj, message):
        try:
            message_object = MessageFactory.generate(message) if message else None
            if (not message_object) or (not self.is_running()):
                logging.error("Could not parse message correctly: {0}".format(message))
                return
            module_object = self.get_valid_module(message_object)
            module_object = module_object if module_object else self._register_module_object(message_object)
            if module_object:
                module_object.execute_module(message_object)
        except Exception as ex:
            logging.exception(ex)

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

import logging
import traceback
from common import consts
from common import modconfig
from common.objfactory import AbstractFactory
from common.objloader import ObjectLoader, ObjectCreator
from common.startable import Startable, StartableManager
from common.msgobject import MessageEvent, AbstractMessage
from core.msghandler import MessageReceiver
from core.msgfactory import MessageFactory
from common.prochandler import CommandProcessor
from multiprocessing.pool import ThreadPool
from configparser import ConfigParser
from jproperties import Properties
from threading import get_ident


class DummyClass(object):
    pass


class ExecutorLoader(ObjectLoader):

    def __init__(self):
        super(ExecutorLoader, self).__init__()
        self._module_dict = dict()

    def _get_klass_from_cache(self, class_name):
        return self._module_dict[class_name] if class_name in self._module_dict else None

    def _register_klass_to_cache(self, class_name, mod):
        self._module_dict[class_name] = mod

    def _validate_classname(self, class_name, props=None):
        return class_name if isinstance(class_name, str) \
            else props.properties[class_name.get_module_id()]

    def _get_existing_klass(self, class_name: str) -> object:
        return self._get_klass_from_cache(class_name)

    def _verify_klass(self, klass, class_name):
        retval = klass if issubclass(klass, CommandProcessor) else None
        self._register_klass_to_cache(class_name, retval) if retval else None
        return retval


class ExecutorCreator(ObjectCreator):

    def __init__(self):
        super(ExecutorCreator, self).__init__()
        self._collection = dict()

    def _configure_instance(self, klass, instance, *args, **kwargs):
        if klass.__name__ not in self._collection:
            self._collection[klass.__name__] = DummyClass()
        parent = self._collection[klass.__name__]
        instance.set_parent(parent)
        return instance


class BaseExecutor(Startable, ExecutorLoader, ExecutorCreator):

    def __init__(self, config=None, module_config=None, module=None):
        super(BaseExecutor, self).__init__(config=config)
        self._module = module
        self._module_config = module_config
        self._command_props = None
        self._event_props = None

    def set_module(self, module):
        self._module = module

    def get_module(self):
        return self._module

    def is_valid_module(self, message_obj):
        return (message_obj.MODULE == self._module) or (self._module == '*')

    def get_command_properties(self):
        return self._command_props

    def get_event_properties(self):
        return self._event_props

    def set_properties(self, cmd_props, event_props):
        self._command_props = cmd_props
        self._event_props = event_props

    def submit_task(self, message_obj):
        raise NotImplementedError()

    def set_module_configuration(self, module_config):
        self._module_config = module_config

    def get_module_configuration(self):
        return self._module_config

    def _configure_instance(self, klass, instance, *args, **kwargs):
        super(BaseExecutor, self)._configure_instance(klass, instance, *args, **kwargs)
        instance.set_configuration(self.get_configuration())
        instance.set_module_configuration(self.get_module_configuration())
        instance.set_message_object(args[0])
        instance.configure()
        return instance

    def _create_obj_module(self, str_mod, message_obj, props):
        klass = self._get_klass(str_mod, props=props)
        return self._create_instance(klass, message_obj)

    def _collect_object_module(self, message_obj: AbstractMessage) -> [[object, str]]:
        props = self.get_event_properties() if isinstance(message_obj, MessageEvent) \
            else self.get_command_properties()
        ret_list = list()
        try:
            if isinstance(message_obj, MessageEvent):
                section_props = props[message_obj.get_module_id()]
                str_mod = None if message_obj.EVENT not in section_props else section_props[message_obj.EVENT]
                list_mod = [str_item.split(":") for str_item in (str_mod.split(",") if str_mod else [])]
                for str_mod, str_func in list_mod:
                    module = self._create_obj_module(str_mod, message_obj, section_props)
                    ret_list.append([module, str_func])
            else:
                module = self._create_obj_module(message_obj, message_obj, props)
                ret_list.append([module, None])
        except Exception as ex:
            logging.exception(ex)
        return ret_list


class ModuleExecutor(BaseExecutor):
    def __init__(self, config=None, module=None, workers=8):
        super(ModuleExecutor, self).__init__(config=config, module=module)
        self._max_processes = workers
        self._pool = None

    def do_configure(self):
        self._max_processes = self._max_processes if self._max_processes > 0 else 4

    def do_start(self):
        self._pool = ThreadPool(processes=self._max_processes)

    def do_stop(self):
        self._pool.terminate()

    def assign_task(self, module: CommandProcessor, message_obj: AbstractMessage, func: str = None):
        self._pool.apply_async(self.do_execute, (module, message_obj, func))

    @staticmethod
    def do_execute(module: CommandProcessor, message_obj: AbstractMessage, func: str):
        logging.debug("Processing {0}".format(message_obj.get_module_id()))
        try:
            module.perform_execute(message_obj, func)
        except Exception as ex:
            logging.exception(ex)
        finally:
            logging.debug("End processing {0}".format(message_obj.get_module_id()))

    def execute_module(self, message_obj: AbstractMessage):
        for module, str_func in self._collect_object_module(message_obj):
            self.assign_task(module, message_obj, str_func)

    def submit_task(self, message_obj: AbstractMessage):
        self.execute_module(message_obj)


class ExecutorFactory(AbstractFactory, ObjectCreator):

    def __init__(self, config=None, klass=None):
        super(ExecutorFactory, self).__init__(config=config)
        self._command_props = None
        self._event_props = None
        self._klass = klass if klass else ModuleExecutor
        self._simple_model = False
        self._available_services = []

    def do_configure(self):
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_COMMAND_FILE)
        self._command_props = Properties()
        with open(config_file, "rb") as file_prop:
            self._command_props.load(file_prop, "utf-8")
        config_file = "{0}/{1}".format(consts.DEFAULT_SCRIPT_PATH, consts.DEFAULT_EVENT_FILE)
        self._event_props = ConfigParser()
        self._event_props.read(config_file)

    def valid_service(self, message_obj: AbstractMessage):
        module_id = message_obj.get_module_id()
        is_available = module_id in self._available_services
        if not is_available:
            props = self._event_props if isinstance(message_obj, MessageEvent) else self._command_props
            is_available = props.has_section(module_id) if isinstance(message_obj, MessageEvent) \
                else module_id in props.keys()
            self._available_services.append(module_id) if is_available else None
        return is_available

    def generate(self, config, message_obj: AbstractMessage):
        module_obj = self._create_instance(self._klass)
        if isinstance(module_obj, BaseExecutor):
            module_name = '*' if self._simple_model else message_obj.MODULE
            module_obj.set_configuration(config)
            module_obj.set_module(module_name)
            module_obj.set_properties(self._command_props, self._event_props)
        return module_obj

    @property
    def simple_model(self) -> bool:
        return self._simple_model

    @simple_model.setter
    def simple_model(self, value: bool) -> None:
        self._simple_model = value


class BaseExecutionManager(StartableManager):

    def __init__(self, config, klass):
        super(BaseExecutionManager, self).__init__(config=config)
        self._executor_factory = ExecutorFactory(config=config, klass=klass)
        self._module_config = None

    def do_configure(self):
        try:
            self._executor_factory.configure()
            self._module_config = modconfig.get_configuration()
        except:
            logging.error(traceback.format_exc())

    def get_valid_module(self, message_obj: AbstractMessage):
        object_list = [obj for obj in self.get_objects() if isinstance(obj, BaseExecutor)]
        for module_obj in object_list:
            if module_obj.is_valid_module(message_obj):
                return module_obj
        return None

    def _register_module_object(self, message_obj: AbstractMessage):
        module_object = None
        if self._executor_factory.valid_service(message_obj):
            module_object = self._executor_factory.generate(self.get_configuration(), message_obj)
            module_object.set_configuration(self.get_configuration())
            module_object.set_module_configuration(self._module_config)
            self.add_object(module_object) if module_object else None
        return module_object

    @property
    def simple_model(self) -> bool:
        return self._executor_factory.simple_model

    @simple_model.setter
    def simple_model(self, value: bool) -> None:
        self._executor_factory.simple_model = value


class MessageExecutionManager(BaseExecutionManager, MessageReceiver):
    """
    Thread based message execution Manager
    """

    def __init__(self, config, klass=ModuleExecutor):
        super(MessageExecutionManager, self).__init__(config=config, klass=klass)

    def process_message(self, message: str):
        try:
            message_object = MessageFactory.generate(message) if message else None
            if message_object:
                module_object = self.get_valid_module(message_object)
                module_object = module_object if module_object else self._register_module_object(message_object)
                module_object.submit_task(message_object) if module_object else None
            else:
                logging.error("Could not extract message correctly: {0}".format(message))
        except Exception as ex:
            logging.exception(ex)

    def on_message_received(self, obj, message: str):
        self.process_message(message) if self.is_running() else None

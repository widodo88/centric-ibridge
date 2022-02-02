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
from threading import RLock


class StartableListener(object):

    def __init__(self, starting=None, started=None, failure=None, stopping=None, stopped=None, configuring=None,
                 configured=None):
        self._starting = starting
        self._started = started
        self._failure = failure
        self._stopping = stopping
        self._stopped = stopped
        self._configuring = configuring
        self._configured = configured

    def on_starting(self, obj):
        if self._starting:
            self._starting(obj)

    def on_started(self, obj):
        if self._started:
            self._started(obj)

    def on_failure(self, obj, exc):
        if self._failure:
            self._failure(obj, exc)

    def on_stopping(self, obj):
        if self._stopping:
            self._stopping(obj)

    def on_stopped(self, obj):
        if self._stopping:
            self._stopping(obj)

    def on_configuring(self, obj, config):
        if self._configuring:
            self._configuring(obj, config)

    def on_configured(self, obj, config):
        if self._configured:
            self._configured(obj, config)


class Startable(object):

    FAILED, STOPPED, STARTING, STARTED, STOPPING, CONFIGURING, CONFIGURED, UNCONFIGURED = -1, 0, 1, 2, 3, 4, 5, 6

    def __init__(self, config=None):
        self._state = Startable.STOPPED
        self._configured = Startable.UNCONFIGURED
        self._enabled = True
        self._listeners = list()
        self._lock = RLock()
        self._configuration = config

    def do_start(self):
        pass

    def do_stop(self):
        pass

    def do_configure(self):
        pass

    def is_enabled(self):
        return self._enabled

    def is_started(self):
        return self._state == Startable.STARTED

    def is_starting(self):
        return self._state == Startable.STARTING

    def is_stopped(self):
        return self._state == Startable.STOPPED

    def is_stopping(self):
        return self._state == Startable.STOPPING

    def is_running(self):
        return self.is_started() or self.is_starting()

    def get_configuration(self):
        return self._configuration

    def set_configuration(self, config):
        self._configuration = config

    def add_listener(self, listener):
        if not isinstance(listener, StartableListener):
            return
        self._listeners.append(listener)

    def remove_listener(self, listener):
        if not isinstance(listener, StartableListener):
            return
        if listener in self._listeners:
            obj_pos = self._listeners.index(listener)
            self._listeners.pop(obj_pos)

    def configure(self):
        self._lock.acquire(blocking=True)
        try:
            if (self._configured == Startable.CONFIGURED) or \
                    (self._state in [Startable.CONFIGURED, Startable.CONFIGURING]):
                return
            self._set_configuring()
            self.do_configure()
            self._set_configured()
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def start(self):
        if self._configured == Startable.UNCONFIGURED:
            self.configure()
        self._lock.acquire(blocking=True)
        try:
            if (not self._enabled) or (self._state in [Startable.STARTED, Startable.STARTING]):
                return
            logging.info("{} - Started".format(self.__class__.__name__))
            self._set_starting()
            self.do_start()
            self._set_started()
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def stop(self):
        self._lock.acquire(blocking=True)
        try:
            if self._state in [Startable.STOPPED, Startable.STOPPING]:
                return
            self._set_stopping()
            self.do_stop()
            self._set_stopped()
            logging.info("{} - Stopped".format(self.__class__.__name__))
        except Exception as exc:
            self._set_failed(exc)
            raise exc
        finally:
            self._lock.release()

    def get_listeners(self):
        return self._listeners

    def _set_configured(self):
        self._state = Startable.CONFIGURED
        self._configured = self._state
        for listener in self._listeners:
            listener.on_configured(self, self._configuration)

    def _set_configuring(self):
        self._state = Startable.CONFIGURING
        self._configured = self._state
        for listener in self._listeners:
            listener.on_configuring(self, self._configuration)

    def _set_failed(self, exc):
        self._state = Startable.FAILED
        for listener in self._listeners:
            listener.on_failure(self, exc)

    def _set_starting(self):
        self._state = Startable.STARTING
        for listener in self._listeners:
            listener.on_starting(self)

    def _set_started(self):
        self._state = Startable.STARTED
        for listener in self._listeners:
            listener.on_started(self)

    def _set_stopping(self):
        self._state = Startable.STOPPING
        for listener in self._listeners:
            listener.on_stopping(self)

    def _set_stopped(self):
        self._state = Startable.STOPPED
        for listener in self._listeners:
            listener.on_stopped(self)


class StartableManager(Startable):

    def __init__(self, config=None):
        super(StartableManager, self).__init__(config)
        self._startable_objects = list()
        self._lock = RLock()

    def get_objects(self):
        return self._startable_objects

    def get_object(self, cls):
        if not cls:
            return
        for item in self._startable_objects:
            if isinstance(item, cls):
                return item

    def add_object(self, obj):
        if (not obj) or (not isinstance(obj, Startable)):
            return
        if obj not in self._startable_objects:
            self._startable_objects.append(obj)

        try:
            if self.is_running():
                obj.set_configuration(self.get_configuration())
                obj.start()
        except Exception as exc:
            raise RuntimeError(exc)

    def remove_object(self, obj):
        if (not obj) or (not isinstance(obj, Startable)):
            return
        if obj in self._startable_objects:
            obj_pos = self._startable_objects.index(obj)
            self._startable_objects.pop(obj_pos)

    def do_configure(self):
        for item in self._startable_objects:
            try:
                item.set_configuration(self.get_configuration())
                item.configure()
            except Exception as exc:
                pass

    def do_start(self):
        for item in self._startable_objects:
            try:
                item.start()
            except Exception as exc:
                pass

    def do_stop(self):
        for item in self._startable_objects:
            try:
                item.stop()
            except Exception as exc:
                pass


class LifeCycleManager(StartableManager):

    VM_DEFAULT = None
    SINGLETON_LOCK = RLock()

    @classmethod
    def get_default_instance(cls):
        cls.SINGLETON_LOCK.acquire(blocking=True)
        try:
            if cls.VM_DEFAULT is None:
                cls.VM_DEFAULT = object.__new__(cls)
                cls.VM_DEFAULT.__init__()

            return cls.VM_DEFAULT
        finally:
            cls.SINGLETON_LOCK.release()
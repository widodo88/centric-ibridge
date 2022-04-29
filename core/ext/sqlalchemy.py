#!usr/bin/env python
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
import typing as t
import re
import sqlalchemy
from threading import Lock, get_ident as _ident_func
from common import consts
from sqlalchemy import inspect
from sqlalchemy.engine.url import make_url
from sqlalchemy.schema import _get_table_key as get_table_key
from sqlalchemy.orm import declarative_base, Query, DeclarativeMeta, declared_attr
from sqlalchemy.orm import scoped_session, sessionmaker, Session, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError
from common.objpreparer import BaseObjectProvider, BaseObjectPreparer
from sqlalchemy.dialects import registry


class SQLAlchemyPreparer(BaseObjectPreparer):

    @classmethod
    def _service_enabled_name(cls):
        return consts.BRIDGE_DATABASE_ENABLED

    @classmethod
    def _get_provider_klass(cls) -> t.Type[BaseObjectProvider]:
        return SQLAlchemyProvider


def _sa_url_set(url, **kwargs):
    try:
        url = url.set(**kwargs)
    except AttributeError:
        for key, value in kwargs.items():
            setattr(url, key, value)
    return url


def _sa_url_query_setdefault(url, **kwargs):
    query = dict(url.query)
    for key, value in kwargs.items():
        query.setdefault(key, value)
    return _sa_url_set(url, query=query)


def to_str(x, charset='utf8', errors='strict'):
    if x is None or isinstance(x, str):
        return x
    if isinstance(x, bytes):
        return x.decode(charset, errors)
    return str(x)


class SQLAlchemyProvider(BaseObjectProvider):

    def __init__(self, config=None):
        super(SQLAlchemyProvider, self).__init__(config=config)
        self._bind_dict = dict()
        self._connectors = dict()
        self._engine_options = dict()
        self.Query = Query
        self.session = self.create_scoped_session()
        self.Model = self.make_declarative_base(Model)
        self._sqla_lock = Lock()

    def do_configure(self):
        config = self.get_configuration()
        registry.register("ibmdb2", "core.ext.sqladialect.ibm_db_sa.ibm_db", "DB2Dialect_ibm_db")
        rest_databases = config[consts.BRIDGE_AVAILABLE_DATABASES] if \
            consts.BRIDGE_AVAILABLE_DATABASES in config else None
        rest_databases = rest_databases if rest_databases else ""
        rest_databases = [service.strip() for service in rest_databases.split(",") if service.strip() not in [None, '']]
        for database in rest_databases:
            key, value = database.split('=', 1)
            self._bind_dict[key] = value

    def get_engine(self, bind=None):
        with self._sqla_lock:
            connector = self._connectors.get(bind)
            if not connector:
                connector = self.make_connector(bind)
                self._connectors[bind] = connector
            return connector.get_engine(self)

    @staticmethod
    def make_connector(bind):
        return EngineConnector(bind)

    @staticmethod
    def create_engine(sa_url, engine_opts):
        return sqlalchemy.create_engine(sa_url, **engine_opts)

    def create_scoped_session(self, options=None):
        options = dict() if options is None else options
        scopefunc = options.pop('scopefunc', _ident_func)
        options.setdefault('query_cls', self.Query)
        return scoped_session(self.create_session(options), scopefunc=scopefunc)

    def create_session(self, options):
        return sessionmaker(class_=SQLASession, db=self, **options)

    def make_declarative_base(self, model, metadata=None):
        if not isinstance(model, DeclarativeMeta):
            model = declarative_base(cls=model, name='Model', metadata=metadata, metaclass=DefaultMeta)
        if metadata is not None and model.metadata is not metadata:
            model.metadata = metadata

        if not getattr(model, 'query_class', None):
            model.query_class = self.Query

        model.query = QueryProperty(self)
        return model

    @staticmethod
    def apply_pool_defaults(options):
        options['pool_size'] = 8
        options['pool_timeout'] = 60
        options['pool_recycle'] = 1800
        options['max_overflow'] = 16
        return options


class QueryProperty(object):
    def __init__(self, provider):
        self.provider = provider

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            return type.query_class(mapper, session=self.provider.session()) if mapper else None
        except UnmappedClassError:
            return None


class SQLASession(Session):

    def get_bind(self, mapper=None, clause=None):
        if mapper is not None:
            persist_selectable = mapper.persist_selectable

            info = getattr(persist_selectable, 'info', {})
            bind_key = info.get('bind_key')
            if bind_key is not None:
                instance = SQLAlchemyProvider.get_default_instance()
                return instance.get_engine(bind=bind_key)
        return super(SQLASession, self).get_bind(mapper, clause)


def should_set_tablename(cls):
    if cls.__dict__.get('__abstract__', False) or \
            not any(isinstance(b, DeclarativeMeta) for b in cls.__mro__[1:]):
        return False

    for base in cls.__mro__:
        if '__tablename__' not in base.__dict__:
            continue
        if isinstance(base.__dict__['__tablename__'], declared_attr):
            return False

        return not (base is cls or base.__dict__.get('__abstract__', False) or not isinstance(base, DeclarativeMeta))
    return True


camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')


def camel_to_snake_case(name):
    def _join(match):
        word = match.group()
        return ('_%s_%s' % (word[:-1], word[-1])).lower() if len(word) > 1 else '_' + word.lower()

    return camelcase_re.sub(_join, name).lstrip('_')


class NameMetaMixin(type):

    def __init__(cls, name, bases, d):
        if should_set_tablename(cls):
            cls.__tablename__ = camel_to_snake_case(cls.__name__)
        super(NameMetaMixin, cls).__init__(name, bases, d)
        if '__tablename__' not in cls.__dict__ and \
                '__table__' in cls.__dict__ and \
                cls.__dict__['__table__'] is None:
            del cls.__table__

    def __table_cls__(cls, *args, **kwargs):
        key = get_table_key(args[0], kwargs.get('schema'))

        if key in cls.metadata.tables:
            return sqlalchemy.Table(*args, **kwargs)

        for arg in args:
            if (isinstance(arg, sqlalchemy.Column) and arg.primary_key) or \
                    isinstance(arg, sqlalchemy.PrimaryKeyConstraint):
                return sqlalchemy.Table(*args, **kwargs)

        for base in cls.__mro__[1:-1]:
            if '__table__' in base.__dict__:
                break
        else:
            return sqlalchemy.Table(*args, **kwargs)

        if '__tablename__' in cls.__dict__:
            del cls.__tablename__


class BindMetaMixin(type):

    def __init__(cls, name, bases, d):
        bind_key = d.pop('__bind_key__', None) or getattr(cls, '__bind_key__', None)
        super(BindMetaMixin, cls).__init__(name, bases, d)
        if bind_key is not None and getattr(cls, '__table__', None) is not None:
            cls.__table__.info['bind_key'] = bind_key


class DefaultMeta(NameMetaMixin, BindMetaMixin, DeclarativeMeta):
    ...


class Model(object):

    _klass = None
    _query = None

    def __repr__(self):
        identity = inspect(self).identity
        if identity is None:
            pk = "(transient {0})".format(id(self))
        else:
            pk = ', '.join(to_str(value) for value in identity)
        return '<{0} {1}>'.format(type(self).__name__, pk)


class EngineConnector(object):

    def __init__(self, bind=None):
        self._bind = bind
        self._connected_for = None
        self._engine = None
        self._lock = Lock()

    def get_uri(self, provider: SQLAlchemyProvider):
        binds = provider._bind_dict
        assert self._bind in binds, 'Bind %r is not specified in the configuration.'
        return binds[self._bind]

    def get_engine(self, provider):
        with self._lock:
            uri = self.get_uri(provider)
            if uri == self._connected_for:
                return self._engine

            sa_url = make_url(uri)
            sa_url, options = self.get_options(sa_url, provider)
            self._engine = rv = provider.create_engine(sa_url, options)
            self._connected_for = uri
            return rv

    def get_options(self, sa_url, provider: SQLAlchemyProvider):
        options = {}
        options = provider.apply_pool_defaults(options)
        options.update(provider._engine_options)
        return sa_url, options

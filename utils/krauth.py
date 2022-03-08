#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Busana Apparel Group. All rights reserved.
#
# This product and it's source code is protected by patents, copyright laws and
# international copyright treaties, as well as other intellectual property
# laws and treaties. The product is licensed, not sold.
#
# The source code and sample programs in this package or parts hereof
# as well as the documentation shall not be copied, modified or redistributed
# without permission, explicit or implied, of the author.
#
try:
    import pybase64 as base64
except:
    import base64
import re
import hashlib
import requests
import threading
from requests.auth import AuthBase
from Crypto.Cipher import AES
from requests.utils import parse_dict_header
from requests.cookies import extract_cookies_to_jar
from requests.compat import builtin_str, is_py2

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-ord(s[-1])]


def to_native_string(string, encoding='ascii'):
    """Given a string object, regardless of type, returns a representation of
    that string in the native string type, encoding and decoding where
    necessary. This assumes ASCII unless told otherwise.
    """
    return string if isinstance(string, builtin_str) else string.encode(encoding) if is_py2 else string.decode(encoding)


class HTTPKrakenZBasicAuth(AuthBase):

    def __init__(self, username, password):
        self.username = username
        self.password = password

        # Keep state in per-thread local storage
        self._thread_local = threading.local()

    def init_per_thread_state(self):
        # Ensure state is initialized just once per-thread
        if hasattr(self._thread_local, 'init'):
            return
        self._thread_local.init = True
        self._thread_local.last_nonce = ''
        self._thread_local.nonce_count = 0
        self._thread_local.chal = {}
        self._thread_local.pos = None
        self._thread_local.num_401_calls = None

    @staticmethod
    def aes_256(x, y):
        y = y.encode('utf-8') if isinstance(y, str) else y
        yl = len(y)
        key = y if yl < 16 else y[:16] if yl < 24 else y[:24] if yl < 32 else y[:32]
        x = bytes(pad(x), 'utf-8')
        cipher = AES.new(hashlib.md5(key).digest(), AES.MODE_ECB)
        return base64.b64encode(cipher.encrypt(x))

    def build_kraken_header(self):
        self._thread_local.nonce_count += 1
        ncvalue = '%08x' % self._thread_local.nonce_count
        A1 = '%s:%s' % (ncvalue, ncvalue)
        HA1 = (hashlib.sha1(A1.encode('utf-8')).hexdigest()[:16]).upper()
        A2 = '%s:%s' % (HA1, self.username)
        HA2 = (hashlib.sha1(A2.encode('utf-8')).hexdigest()[:16]).upper()

        PE2 = self.aes_256(self.password, HA2)
        E1 = '%s:%s' % (self.username, PE2.decode('UTF-8'))
        PE1 = self.aes_256(E1, HA1)
        E2 = '%s@%s' % (ncvalue, PE1.decode('UTF-8'))
        PE3 = base64.b64encode(E2.encode()).strip()
        return 'zbasic ' + to_native_string(PE3.decode('UTF-8'))

    def __eq__(self, other):
        return all([
            self.username == getattr(other, 'username', None),
            self.password == getattr(other, 'password', None)
        ])

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        self.init_per_thread_state()
        r.headers['Authorization'] = self.build_kraken_header()
        return r


class HTTPKrakenXBasicAuth(HTTPKrakenZBasicAuth):
    """Attaches HTTP Kraken XBasicAuth Authentication to a given Request object."""

    def __init__(self, username, password):
        super(HTTPKrakenXBasicAuth, self).__init__(username, password)

    def build_kraken_header(self):
        """
        :rtype: str
        """

        nonce = self._thread_local.chal['nonce']
        nc = self._thread_local.chal.get('nc')

        if nonce == self._thread_local.last_nonce:
            self._thread_local.nonce_count += 1
        else:
            self._thread_local.nonce_count = 1
        ncvalue = '%08x' % self._thread_local.nonce_count
        A1 = '%s:%s' % (nonce, ncvalue)
        HA1 = (hashlib.sha1(A1.encode('utf-8')).hexdigest()[:16]).upper()
        A2 = '%s:%s' % (HA1, self.username)
        HA2 = (hashlib.sha1(A2.encode('utf-8')).hexdigest()[:16]).upper()

        PE2 = self.aes_256(self.password, HA2)
        E1 = '%s:%s' % (self.username, PE2.decode('UTF-8'))
        PE1 = self.aes_256(E1, HA1)
        E2 = '%s:%s@%s' % (nonce, ncvalue, PE1.decode('UTF-8'))
        PE3 = base64.b64encode(E2.encode()).strip()
        return 'xbasic ' + to_native_string(PE3.decode('UTF-8'))

    def handle_redirect(self, r, **kwargs):
        """Reset num_401_calls counter on redirects."""
        if r.is_redirect:
            self._thread_local.num_401_calls = 1

    def handle_401(self, r, **kwargs):
        """
        Takes the given response and tries digest-auth, if needed.

        :rtype: requests.Response
        """

        # If response is not 4xx, do not auth
        # See https://github.com/requests/requests/issues/3772
        if not 400 <= r.status_code < 500:
            self._thread_local.num_401_calls = 1
            return r

        if self._thread_local.pos is not None:
            # Rewind the file position indicator of the body to where
            # it was to resend the request.
            r.request.body.seek(self._thread_local.pos)

        s_auth = r.headers.get('www-authenticate', '')
        if 'xbasic' in s_auth.lower() and self._thread_local.num_401_calls < 2:

            self._thread_local.num_401_calls += 1
            pat = re.compile(r'basic ', flags=re.IGNORECASE)
            self._thread_local.chal = parse_dict_header(pat.sub('', s_auth, count=1))

            # Consume content and release the original connection
            # to allow our new request to reuse the same one.
            r.content
            r.close()
            prep = r.request.copy()
            extract_cookies_to_jar(prep._cookies, r.request, r.raw)
            prep.prepare_cookies(prep._cookies)

            prep.headers['Authorization'] = self.build_kraken_header()
            _r = r.connection.send(prep, **kwargs)
            _r.history.append(r)
            _r.request = prep

            return _r

        self._thread_local.num_401_calls = 1
        return r

    def __call__(self, r):
        # Initialize per-thread state, if needed
        self.init_per_thread_state()

        # If we have a saved nonce, skip the 401
        if self._thread_local.last_nonce:
            r.headers['Authorization'] = self.build_kraken_header()
        try:
            self._thread_local.pos = r.body.tell()
        except AttributeError:
            # In the case of HTTPDigestAuth being reused and the body of
            # the previous request was a file-like object, pos has the
            # file position of the previous body. Ensure it's set to
            # None.
            self._thread_local.pos = None
        r.register_hook('response', self.handle_401)
        r.register_hook('response', self.handle_redirect)
        self._thread_local.num_401_calls = 1

        return r

    def __eq__(self, other):
        return all([
            self.username == getattr(other, 'username', None),
            self.password == getattr(other, 'password', None)
        ])

    def __ne__(self, other):
        return not self == other


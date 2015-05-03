import json

import requests
from urlobject import URLObject as URL

from .session import Session
from .lazy_query import LazyQuery
from .test import Test
from .error import Error
from ._compat import iteritems
from sentinels import NOTHING

_TYPES_BY_TYPENAME = {
    'session': Session,
    'test': Test,
    'error': Error
}


class Backslash(object):

    def __init__(self, url):
        super(Backslash, self).__init__()
        self.api = API(self, url)
        if not url.startswith('http'):
            url = 'http://{0}'.format(url)
        self._url = URL(url)

    def report_session_start(self, logical_id=NOTHING,
                             hostname=NOTHING,
                             product_name=NOTHING,
                             product_version=NOTHING,
                             product_revision=NOTHING):
        """Reports a new session starting

        :rtype: A session object representing the reported session
        """
        return self.api.call_function('report_session_start', {
            'hostname': hostname,
            'logical_id': logical_id,
            'product_name': product_name,
            'product_version': product_version,
            'product_revision': product_revision
        })

    def query_sessions(self):
        """Queries sessions stored on the server

        :rtype: A lazy query object
        """
        return LazyQuery(self, '/rest/sessions')

    def query_tests(self):
        """Queries tests stored on the server (directly, not via a session)

        :rtype: A lazy query object
        """
        return LazyQuery(self, '/rest/tests')

class API(object):

    def __init__(self, client, url):
        super(API, self).__init__()
        self.client = client
        self.url = URL(url)

    def call_function(self, name, params=None):
        resp = requests.post(
            self.url.add_path('api').add_path(name),
            data=self._serialize_params(params),
            headers={'Content-type': 'application/json'},
        )
        resp.raise_for_status()

        return self._normalize_return_value(resp)

    def get(self, path, raw=False):
        resp = requests.get(self.url.add_path(path))
        resp.raise_for_status()
        if raw:
            return resp.json()
        else:
            return self._normalize_return_value(resp)

    def _normalize_return_value(self, response):
        result = response.json()['result']
        if result is None:
            return None
        assert isinstance(result, dict) and 'type' in result
        return self.build_api_object(result)

    def build_api_object(self, result):
        return self._get_objtype(result)(self.client, result)

    def _get_objtype(self, json_object):
        typename = json_object['type']
        returned = _TYPES_BY_TYPENAME.get(typename)
        if returned is None:
            raise NotImplementedError()  # pragma: no cover
        return returned

    def _serialize_params(self, params):
        if params is None:
            params = {}

        returned = {}
        for param_name, param_value in iteritems(params):
            if param_value is NOTHING:
                continue
            returned[param_name] = param_value
        return json.dumps(returned)

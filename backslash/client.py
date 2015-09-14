import json

import gossip
import requests
from urlobject import URLObject as URL

from .session import Session
from .lazy_query import LazyQuery
from .test import Test
from .error import Error
from .comment import Comment
from ._compat import iteritems
from .utils import raise_for_status
from sentinels import NOTHING

_TYPES_BY_TYPENAME = {
    'session': Session,
    'test': Test,
    'error': Error,
    'comment': Comment,
}


class Backslash(object):

    def __init__(self, url, runtoken):
        super(Backslash, self).__init__()
        if not url.startswith('http'):
            url = 'http://{0}'.format(url)
        self._url = URL(url)
        self.api = API(self, url, runtoken)

    def delete_comment(self, comment_id):
        self.api.call_function('delete_comment', {'comment_id': comment_id})

    def report_session_start(self, logical_id=NOTHING,
                             hostname=NOTHING,
                             product_name=NOTHING,
                             product_version=NOTHING,
                             product_revision=NOTHING,
                             total_num_tests=NOTHING,
                             user_email=NOTHING,
                             metadata=NOTHING,
    ):
        """Reports a new session starting

        :rtype: A session object representing the reported session
        """
        returned = self.api.call_function('report_session_start', {
            'hostname': hostname,
            'logical_id': logical_id,
            'product_name': product_name,
            'product_version': product_version,
            'product_revision': product_revision,
            'total_num_tests': total_num_tests,
            'user_email': user_email,
            'metadata': metadata,
        })
        gossip.trigger('backslash.session_start', session=returned)
        return returned

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

    def __init__(self, client, url, runtoken):
        super(API, self).__init__()
        self.client = client
        self.url = URL(url)
        self.runtoken = runtoken
        self.session = requests.Session()
        self.session.headers.update({
            'Content-type': 'application/json',
            'X-Backslash-run-token': self.runtoken})

    def call_function(self, name, params=None):
        resp = self.session.post(
            self.url.add_path('api').add_path(name),
            data=self._serialize_params(params),
        )
        raise_for_status(resp)

        return self._normalize_return_value(resp)

    def get(self, path, raw=False):
        resp = requests.get(self.url.add_path(path))
        raise_for_status(resp)
        if raw:
            return resp.json()
        else:
            return self._normalize_return_value(resp)

    def _normalize_return_value(self, response):
        result = response.json()['result']
        if result is None:
            return None
        assert isinstance(result, dict)
        if 'type' in result:
            return self.build_api_object(result)
        return result

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


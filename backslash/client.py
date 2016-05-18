# pylint: disable=no-member
import gzip
import json
import random
import time

import logbook
import requests

from sentinels import NOTHING
from urlobject import URLObject as URL

from ._compat import iteritems, BytesIO, TextIOWrapper
from .comment import Comment
from .error import Error
from .lazy_query import LazyQuery
from .session import Session
from .test import Test
from .utils import raise_for_status
from .warning import Warning

_TYPES_BY_TYPENAME = {
    'session': Session,
    'test': Test,
    'error': Error,
    'warning': Warning,
    'comment': Comment,
}

_RETRY_STATUS_CODES = set([
    requests.codes.bad_gateway,
    requests.codes.gateway_timeout,
])

_logger = logbook.Logger(__name__)


_COMPRESS_THRESHOLD = 4 * 1024
_MAX_PARAMS_SIZE = 1024 * 1024 # 1Mb

class BackslashClientException(Exception):
    pass

class ParamsTooLarge(BackslashClientException):
    pass


class Backslash(object):

    def __init__(self, url, runtoken):
        super(Backslash, self).__init__()
        if not url.startswith('http'):
            url = 'http://{0}'.format(url)
        self._url = URL(url)
        self.api = API(self, url, runtoken)

    def toggle_user_role(self, user_id, role):
        return self.api.call_function('toggle_user_role', {'user_id': user_id, 'role': role})

    def get_user_run_tokens(self, user_id):
        return self.api.call_function('get_user_run_tokens', {'user_id': user_id})

    def delete_comment(self, comment_id):
        self.api.call_function('delete_comment', {'comment_id': comment_id})

    def report_session_start(self, logical_id=NOTHING,
                             hostname=NOTHING,
                             total_num_tests=NOTHING,
                             user_email=NOTHING,
                             metadata=NOTHING,
                             keepalive_interval=NOTHING,
                             subjects=NOTHING,
                             infrastructure=NOTHING,
    ):
        """Reports a new session starting

        :rtype: A session object representing the reported session
        """
        returned = self.api.call_function('report_session_start', {
            'hostname': hostname,
            'logical_id': logical_id,
            'total_num_tests': total_num_tests,
            'user_email': user_email,
            'metadata': metadata,
            'keepalive_interval': keepalive_interval,
            'subjects': subjects,
            'infrastructure': infrastructure,
        })
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

    def query(self, path, **kwargs):
        return LazyQuery(self, path, **kwargs)

class API(object):

    def __init__(self, client, url, runtoken):
        super(API, self).__init__()
        self.client = client
        self.url = URL(url)
        self.runtoken = runtoken
        self.session = requests.Session()
        self.session.headers.update({
            'X-Backslash-run-token': self.runtoken})

    def call_function(self, name, params=None):
        is_compressed, data = self._serialize_params(params)
        headers = {'Content-type': 'application/json'}
        if is_compressed:
            headers['Content-encoding'] = 'gzip'

        for _ in self._iter_retries():

            try:
                resp = self.session.post(
                    self.url.add_path('api').add_path(name), data=data, headers=headers)
            except (requests.ConnectionError,):
                continue

            if resp.status_code not in _RETRY_STATUS_CODES:
                break
        else:
            raise BackslashClientException('Maximum number of retries exceeded for calling Backslash API')

        raise_for_status(resp)

        return self._normalize_return_value(resp)

    def _iter_retries(self, timeout=30, sleep_range=(3, 10)):
        start_time = time.time()
        end_time = start_time + timeout
        while True:
            yield
            if time.time() < end_time:
                time.sleep(random.randrange(*sleep_range))

    def get(self, path, raw=False, params=None):
        resp = self.session.get(self.url.add_path(path), params=params)
        raise_for_status(resp)
        if raw:
            return resp.json()
        else:
            return self._normalize_return_value(resp)


    def _normalize_return_value(self, response):
        json = response.json()
        if json is None:
            return None
        result = response.json().get('result')
        if result is None:
            return json
        if isinstance(result, dict) and 'type' in result:
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
        compressed = False
        returned = json.dumps(returned)
        if len(returned) > _COMPRESS_THRESHOLD:
            compressed = True
            returned = self._compress(returned)
        if len(returned) > _MAX_PARAMS_SIZE:
            raise ParamsTooLarge()
        return compressed, returned

    def _compress(self, data):
        s = BytesIO()

        with gzip.GzipFile(fileobj=s, mode='wb') as f:
            with TextIOWrapper(f) as w:
                w.write(data)

        return s.getvalue()

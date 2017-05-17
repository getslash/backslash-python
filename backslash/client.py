# pylint: disable=no-member

import logbook

from sentinels import NOTHING
from urlobject import URLObject as URL

from .api import API
from .compatibility import Compatibility
from .lazy_query import LazyQuery


_logger = logbook.Logger(__name__)


class Backslash(object):

    def __init__(self, url, runtoken):
        super(Backslash, self).__init__()
        if not url.startswith('http'):
            url = 'http://{0}'.format(url)
        self._url = URL(url)
        self.api = API(self, url, runtoken)

    @property
    def url(self):
        return self._url

    def toggle_user_role(self, user_id, role):
        return self.api.call_function('toggle_user_role', {'user_id': user_id, 'role': role})

    def get_user_run_tokens(self, user_id):
        return self.api.call_function('get_user_run_tokens', {'user_id': user_id})

    def delete_comment(self, comment_id):
        self.api.call_function('delete_comment', {'comment_id': comment_id})

    def report_session_start(self, logical_id=NOTHING,
                             parent_logical_id=NOTHING,
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
        params = {
            'hostname': hostname,
            'logical_id': logical_id,
            'total_num_tests': total_num_tests,
            'user_email': user_email,
            'metadata': metadata,
            'keepalive_interval': keepalive_interval,
            'subjects': subjects,
            'infrastructure': infrastructure,
        }
        if parent_logical_id is not None:
            supports_parent_logical_id = (self.api.info().endpoints.report_session_start.version >= 2)

            if supports_parent_logical_id:
                params['parent_logical_id'] = parent_logical_id

        returned = self.api.call_function('report_session_start', params)
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

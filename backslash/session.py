from sentinels import NOTHING

from .api_object import APIObject
from .lazy_query import LazyQuery

class Session(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_session_end', {'id': self.id, 'duration': duration})

    def report_test_start(self, name=NOTHING, test_logical_id=NOTHING):
        return self.client.api.call_function('report_test_start', {'session_id': self.id,
                                                                   'test_logical_id': test_logical_id, 'name': name})

    def set_product(self, name, version=NOTHING, revision=NOTHING):
        return self.client.api.call_function('set_product', {'id': self.id, 'name': name,
                                                             'version': version, 'revision': revision })

    def set_user(self, user_name):
        return self.client.api.call_function('set_session_user', {'id': self.id, 'user_name': user_name})

    def add_metadata(self, metadata):
        return self.client.api.call_function('add_session_metadata', {'id': self.id, 'metadata': metadata})

    def add_error_data(self, exception, exception_type, traceback, timestamp=NOTHING):
        return self.client.api.call_function('add_session_error_data', {'id': self.id,
                                                                        'exception': exception,
                                                                        'exception_type': exception_type,
                                                                        'traceback': traceback,
                                                                        'timestamp': timestamp
                                                                        })

    def edit_status(self, status):
        return self.client.api.call_function('edit_session_status', {'id': self.id, 'status': status})

    def query_tests(self):
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/sessions/{0}/tests'.format(self.id))

    def query_errors(self):
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/errors', query_params={'session_id': self.id})
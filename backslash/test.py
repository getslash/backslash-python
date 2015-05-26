from sentinels import NOTHING

from .api_object import APIObject
from .lazy_query import LazyQuery

class Test(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_test_end', {'id': self.id, 'duration': duration})

    def mark_skipped(self):
        self.client.api.call_function('report_test_skipped', {'id': self.id})

    def mark_interrupted(self):
        self.client.api.call_function('report_test_interrupted', {'id': self.id})

    def add_error(self):
        return self.client.api.call_function('add_test_error', {'id': self.id})

    def add_failure(self):
        return self.client.api.call_function('add_test_failure', {'id': self.id})

    def add_metadata(self, metadata):
        return self.client.api.call_function('add_test_metadata', {'id': self.id, 'metadata': metadata})

    def set_conclusion(self, conclusion):
        return self.client.api.call_function('set_test_conclusion', {'id': self.id, 'conclusion': conclusion})

    def add_error_data(self, exception, exception_type, traceback, timestamp=NOTHING):
        return self.client.api.call_function('add_test_error_data', {'id': self.id,
                                                                     'exception': exception,
                                                                     'exception_type': exception_type,
                                                                     'traceback': traceback,
                                                                     'timestamp': timestamp
                                                                     })

    def edit_status(self, status):
        return self.client.api.call_function('edit_test_status', {'id': self.id, 'status': status})

    def query_errors(self):
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/errors', query_params={'test_id': self.id})

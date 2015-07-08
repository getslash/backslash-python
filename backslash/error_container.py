from sentinels import NOTHING


class ErrorContainer(object):

    def add_error(self, exception, exception_type, traceback, timestamp=NOTHING):
        return self.client.api.call_function('add_error', {self._get_id_key(): self.id,
                                                           'exception': exception,
                                                           'exception_type': exception_type,
                                                           'traceback': traceback,
                                                           'timestamp': timestamp
                                                       })
    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

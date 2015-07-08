from sentinels import NOTHING


class ErrorContainer(object):

    def add_error(self, message, exception_type=NOTHING, traceback=NOTHING, timestamp=NOTHING):
        return self.client.api.call_function('add_error', {self._get_id_key(): self.id,
                                                           'message': message,
                                                           'exception_type': exception_type,
                                                           'traceback': traceback,
                                                           'timestamp': timestamp
                                                       })
    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

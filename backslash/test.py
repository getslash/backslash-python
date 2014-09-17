from sentinels import NOTHING

from .api_object import APIObject


class Test(APIObject):

    def report_end(self, duration=NOTHING, skipped=False):
        self.client.api.call_function('report_test_end', {'id': self.id, 'duration': duration, 'skipped': skipped})

    def add_error(self):
        return self.client.api.call_function('test_add_error', {'id': self.id})

    def add_failure(self):
        return self.client.api.call_function('test_add_failure', {'id': self.id})

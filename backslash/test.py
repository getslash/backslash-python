from sentinels import NOTHING

from .api_object import APIObject


class Test(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_test_end', {'id': self.id, 'duration': duration})

    def get_status(self):
        return self.client.api.call_function('get_test_status', {'id': self.id})

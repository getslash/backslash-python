from sentinels import NOTHING

from .api_object import APIObject


class Test(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_test_end', {'id': self.id, 'duration': duration})

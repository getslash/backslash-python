from sentinels import NOTHING

from .api_object import APIObject


class Test(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_test_end', {'logical_id': self.logical_id, 'duration': duration})

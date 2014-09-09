from sentinels import NOTHING

from .api_object import APIObject


class Session(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_session_end', {'id': self.id, 'duration': duration})

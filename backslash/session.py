from sentinels import NOTHING

from .api_object import APIObject


class Session(APIObject):

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_session_end', {'logical_id': self.logical_id, 'duration': duration})

    def report_test_start(self, test_logical_id, name=NOTHING):
        return self.client.api.call_function('report_test_start', {'session_logical_id': self.logical_id,
                                                                   'test_logical_id': test_logical_id, 'name': name})

    def set_product(self, name, version=None, revision=None):
        return self.client.api.call_function('set_product', {'logical_id': self.logical_id, 'name': name,
                                                             'version': version, 'revision': revision })
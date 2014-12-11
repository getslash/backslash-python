from sentinels import NOTHING

from .api_object import APIObject


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
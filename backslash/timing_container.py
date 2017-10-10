class TimingContainer(object):

    def report_timing_start(self, name):
        self._report('start', name)

    def report_timing_end(self, name):
        self._report('end', name)

    def _report(self, start_stop, name):
        kwargs = {'name': name}
        kwargs.update(self._get_identity_kwargs())
        self.client.api.call_function('report_timing_{}'.format(start_stop), kwargs) # pylint: disable=no-member

    def _get_identity_kwargs(self):
        if self.type.lower() == 'session': # pylint: disable=no-member
            return {'session_id': self.id} # pylint: disable=no-member

        return {'test_id': self.id, 'session_id': self.session_id} # pylint: disable=no-member

    def get_timings(self):
        return self.client.api.call.get_timings(**self._get_identity_kwargs()) # pylint: disable=no-member

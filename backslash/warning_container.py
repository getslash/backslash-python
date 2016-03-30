from sentinels import NOTHING

from .contrib.utils import normalize_file_path
from .lazy_query import LazyQuery


class WarningContainer(object):


    def add_warning(self, message, filename=NOTHING, lineno=NOTHING, timestamp=NOTHING):
        return self.client.api.call_function('add_warning', {self._get_id_key(): self.id,
                                                           'message': message,
                                                           'lineno': lineno,
                                                           'filename': normalize_file_path(filename),
                                                           'timestamp': timestamp,
                                                       })

    def query_warnings(self):
        return LazyQuery(self.client, '/rest/warnings', query_params={self._get_id_key(): self.id})

    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

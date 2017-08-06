import gzip
import json
import tempfile

from ._compat import TextIOWrapper

import logbook
from sentinels import NOTHING


_logger = logbook.Logger(__name__)


class ErrorContainer(object):

    def add_error(self, message, exception_type=NOTHING, traceback=NOTHING, timestamp=NOTHING, is_failure=NOTHING, exception_attrs=NOTHING):

        kwargs = {self._get_id_key(): self.id,  # pylint: disable=no-member
                  'message': message,
                  'exception_type': exception_type,
                  'is_failure': is_failure,
                  'timestamp': timestamp
                  }

        add_error_version = self.client.api.info().endpoints.add_error.version # pylint: disable=no-member
        has_streaming_upload = add_error_version >= 2
        has_exception_attrs = add_error_version >= 3

        if not has_streaming_upload:
            if traceback is not NOTHING:
                kwargs['traceback'] = traceback
            traceback_info = NOTHING
        else:
            if has_exception_attrs:
                traceback_info = {'traceback': None if traceback is NOTHING else traceback,
                                  'exception': {
                                      'attributes': None if  exception_attrs is NOTHING else exception_attrs
                                  }
                }
            else:
                traceback_info = traceback

        returned = self.client.api.call_function('add_error', kwargs) # pylint: disable=no-member

        if has_streaming_upload and traceback_info is not NOTHING:
            self._compress_traceback(returned, traceback_info)

        return returned

    def _compress_traceback(self, error, traceback_info):
        traceback_url = error.api_url.add_path('traceback')
        with tempfile.TemporaryFile(mode='w+b') as traceback_file:
            try:
                with gzip.GzipFile(fileobj=traceback_file, mode='w+b') as compressed_file_raw:
                    with TextIOWrapper(compressed_file_raw) as compressed_file:
                        json.dump(traceback_info, compressed_file)
            except IOError:
                _logger.error('Unable to compress traceback on disk. Reporting error without traceback', exc_info=True)
                return

            traceback_file.seek(0)
            resp = self.client.api.session.put(traceback_url, data=traceback_file) # pylint: disable=no-member
            resp.raise_for_status()
        error.refresh()

    def add_failure(self, message, **kwargs):
        return self.add_error(message, is_failure=True, **kwargs)

    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

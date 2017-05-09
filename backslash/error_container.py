import gzip
import json
import tempfile

from ._compat import TextIOWrapper

from sentinels import NOTHING


class ErrorContainer(object):

    def add_error(self, message, exception_type=NOTHING, traceback=NOTHING, timestamp=NOTHING, is_failure=NOTHING):

        kwargs = {self._get_id_key(): self.id,
                  'message': message,
                  'exception_type': exception_type,
                  'is_failure': is_failure,
                  'timestamp': timestamp
                  }

        has_streaming_upload = self.client.api.info().endpoints.add_error.version >= 2

        if traceback is not NOTHING and not has_streaming_upload:
            kwargs['traceback'] = traceback

        returned = self.client.api.call_function('add_error', kwargs) # pylint: disable=no-member

        if has_streaming_upload and traceback is not NOTHING:
            traceback_url = returned.api_url.add_path('traceback')
            with tempfile.TemporaryFile(mode='w+b') as traceback_file:
                with gzip.GzipFile(fileobj=traceback_file, mode='w+b') as compressed_file_raw:
                    with TextIOWrapper(compressed_file_raw) as compressed_file:
                        json.dump(traceback, compressed_file)

                traceback_file.seek(0)
                resp = self.client.api.session.put(traceback_url, data=traceback_file) # pylint: disable=no-member
                resp.raise_for_status()
            returned.refresh()
        return returned

    def add_failure(self, message, **kwargs):
        return self.add_error(message, is_failure=True, **kwargs)

    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

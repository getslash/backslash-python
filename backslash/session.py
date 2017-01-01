# pylint: disable=no-member
from sentinels import NOTHING

from .api_object import APIObject
from .archiveable import Archiveable
from .commentable import Commentable
from .error_container import ErrorContainer
from .related_entity_container import RelatedEntityContainer
from .warning_container import WarningContainer
from .lazy_query import LazyQuery
from .metadata_holder import MetadataHolder


class Session(APIObject, MetadataHolder, ErrorContainer, WarningContainer, Archiveable, Commentable, RelatedEntityContainer):

    @property
    def ui_url(self):
        return self.client.url + '#/sessions/{}'.format(self.logical_id or self.id)

    def report_end(self, duration=NOTHING):
        self.client.api.call_function('report_session_end', {'id': self.id, 'duration': duration})

    def send_keepalive(self):
        self.client.api.call_function('send_keepalive', {'session_id': self.id})

    def report_test_start(self, name, file_name=NOTHING, class_name=NOTHING, test_logical_id=NOTHING, scm=NOTHING, file_hash=NOTHING, scm_revision=NOTHING, scm_dirty=NOTHING, is_interactive=NOTHING, variation=NOTHING, metadata=NOTHING, test_index=NOTHING):


        params = {'session_id': self.id,
             'name': name,
             'scm': scm,
             'file_hash': file_hash,
             'scm_revision': scm_revision,
             'scm_dirty': scm_dirty,
             'class_name': class_name,
             'file_name': file_name,
             'is_interactive': is_interactive,
             'variation': variation,
             'test_logical_id': test_logical_id,
             'test_index': test_index,
        }

        if metadata is not NOTHING:
            supports_inline_metadata = (self.client.api.info().endpoints.report_test_start.version >= 2)

            if supports_inline_metadata:
                params['metadata'] = metadata

        returned = self.client.api.call_function(
            'report_test_start', params
        )

        if metadata is not NOTHING and not supports_inline_metadata:
            returned.set_metadata_dict(metadata)

        return returned


    def report_in_pdb(self):
        self.client.api.call_function('report_in_pdb', {'session_id': self.id})

    def report_not_in_pdb(self):
        self.client.api.call_function('report_not_in_pdb', {'session_id': self.id})

    def add_subject(self, name, product=NOTHING, version=NOTHING, revision=NOTHING):
        return self.client.api.call_function(
            'add_subject',
            {'session_id': self.id, 'name': name, 'product': product, 'version': version, 'revision': revision})

    def edit_status(self, status):
        return self.client.api.call_function('edit_session_status', {'id': self.id, 'status': status})

    def query_tests(self):
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/sessions/{0}/tests'.format(self.id))

    def query_errors(self):
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/errors', query_params={'session_id': self.id})

    def toggle_investigated(self):
        return self.client.api.call_function('toggle_investigated', {'session_id': self.id})

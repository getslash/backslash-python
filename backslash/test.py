from sentinels import NOTHING

from .api_object import APIObject
from .commentable import Commentable
from .error_container import ErrorContainer
from .related_entity_container import RelatedEntityContainer
from .warning_container import WarningContainer
from .lazy_query import LazyQuery
from .metadata_holder import MetadataHolder
from .timing_container import TimingContainer


class Test(APIObject, MetadataHolder, ErrorContainer, WarningContainer, Commentable, RelatedEntityContainer, TimingContainer):

    @property
    def ui_url(self) -> str:
        return self.client.get_ui_url(f'sessions/{self.session_display_id}/tests/{self.logical_id or self.id}')

    def report_end(self, duration=NOTHING) -> None:
        self.client.api.call_function('report_test_end', {'id': self.id, 'duration': duration})

    def mark_skipped(self, reason=None) -> None:
        self.client.api.call_function('report_test_skipped', {'id': self.id, 'reason': reason})

    def report_interrupted(self) -> None:
        self.client.api.call_function('report_test_interrupted', {'id': self.id})

    def query_errors(self) -> LazyQuery:
        """Queries tests of the current session

        :rtype: A lazy query object
        """
        return LazyQuery(self.client, '/rest/errors', query_params={'test_id': self.id})

    def get_session(self):
        return self.client.api.get(f'/rest/sessions/{self.session_id}')

    def get_parent(self):
        return self.get_session()

    def update_status_description(self, description: str):
        return self.client.api.call_function('update_status_description', {'test_id': self.id, 'description': description})

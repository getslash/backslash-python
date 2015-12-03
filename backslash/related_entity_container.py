class RelatedEntityContainer(object):

    def add_related_entity(self, entity_type, entity_name):
        # pylint: disable=no-member
        self.client.api.call_function('add_related_entity', {
            self._get_id_key(): self.id,
            'type': entity_type,
            'name': entity_name,
            })

    def _get_id_key(self):
        if type(self).__name__ == 'Test':
            return 'test_id'
        return 'session_id'

class Archiveable(object):

    def toggle_archived(self):
        self.client.api.call_function('toggle_archived', {self._get_id_key(): self.id})

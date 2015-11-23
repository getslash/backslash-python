class MetadataHolder(object):

    def set_metadata(self, key, value):
        self.client.api.call_function('set_metadata', {
            'entity_type': self._data['type'],
            'entity_id': self.id,
            'key': key,
            'value': value
            })

    def set_metadata_dict(self, metadata_dict):
        self.client.api.call_function('set_metadata_dict', {
            'entity_type': self._data['type'],
            'entity_id': self.id,
            'metadata': metadata_dict,
            })


    def get_metadata(self):
        return self.client.api.call_function('get_metadata', {
            'entity_type': self._data['type'],
            'entity_id': self.id,
        })

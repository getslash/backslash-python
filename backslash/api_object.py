
class APIObject(object):

    def __init__(self, client, json_data):
        super(APIObject, self).__init__()
        self.client = client
        self._data = json_data

    @property
    def api_url(self):
        return self.client.url.add_path(self.api_path)

    @property
    def ui_url(self):
        raise NotImplementedError() # pragma: no cover

    def __eq__(self, other):
        if not isinstance(other, APIObject):
            return NotImplemented
        return self.client is other.client and self._data == other._data

    def __ne__(self, other):
        return not (self == other)

    def __getattr__(self, name):
        try:
            return self.__dict__['_data'][name]
        except KeyError:
            raise AttributeError(name)

    def refresh(self):
        prev_id = self.id
        self._data = self._fetch()
        assert self.id == prev_id
        return self

    def _fetch(self):
        return self.client.api.get(self.api_path, raw=True)[self._data['type']]

    def __repr__(self):
        return '<API:{data[type]}:{data[id]}>'.format(data=self._data)

    def without_fields(self, field_names):
        new_data = dict((field_name, field_value)
                        for field_name, field_value in self._data.items()
                        if field_name not in field_names)
        return type(self)(self.client, new_data)

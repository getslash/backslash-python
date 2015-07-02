
class APIObject(object):

    def __init__(self, client, json_data):
        super(APIObject, self).__init__()
        self.client = client
        self._data = json_data

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
        self._data = self._fetch()
        return self

    def _fetch(self):
        return self.client.api.get(self.api_path, raw=True)[self._data['type']]

    def __repr__(self):
        return '<API:{data[type]}:{data[id]}>'.format(data=self._data)

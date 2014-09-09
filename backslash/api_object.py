
class APIObject(object):

    def __init__(self, client, json_data):
        super(APIObject, self).__init__()
        self.client = client
        self._data = json_data

    def __getattr__(self, name):
        try:
            return self._data[name]
        except LookupError:
            raise AttributeError(name)

    def refresh(self):
        self._data = self._fetch()

    def _fetch(self):
        return self.client.api.get(self.api_path, raw=True)['result']

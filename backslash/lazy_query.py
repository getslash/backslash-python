import collections
import itertools

from sentinels import NOTHING

from .utils import raise_for_status


class LazyQuery():

    def __init__(self, client, path=None, url=None, query_params=None, page_size=100):
        super().__init__()
        self._client = client
        if url is None:
            url = client.api.url
        if path is not None:
            url = url.add_path(path)
        if query_params is not None:
            for (param, value) in query_params.items():
                url = url.add_query_param(param, str(value))
        self._url = url
        self._fetched = collections.defaultdict(lambda: NOTHING)
        self._total_num_objects = None
        self._page_size = page_size
        self._typename = None

    def all(self):
        return list(self)

    def filter(self, *filter_objects, **fields):
        returned_url = self._url
        for filter_object in filter_objects:
            returned_url = filter_object.add_to_url(returned_url)
        for field_name, field_value in fields.items():
            returned_url = returned_url.add_query_param(field_name, str(field_value))
        return LazyQuery(self._client, url=returned_url, page_size=self._page_size)

    def __repr__(self):
        return f'<Query {str(self._url)!r}>'

    def __iter__(self):
        for i in itertools.count():
            item = self._fetch_index(i)
            if item is NOTHING:
                break
            yield item

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            raise NotImplementedError() # pragma: no cover
        if idx < 0:
            if idx < -len(self):
                raise IndexError()
            idx = len(self) + idx
        returned = self._fetch_index(idx)
        if returned is NOTHING:
            raise IndexError(idx)
        return returned

    def _fetch_index(self, index):
        returned = self._fetched[index]
        if returned is NOTHING:
            page_index = (index // self._page_size) + 1
            self._fetch_page(page_index)
            returned = self._fetched[index]
        return returned

    def _fetch_page(self, page_index):
        assert page_index != 0
        response = self._client.api.session.get(self._url.add_query_param(
            'page', str(page_index)).add_query_param('page_size', str(self._page_size)))
        raise_for_status(response)
        response_data = response.json()
        keys = [key for key in response_data if key != 'meta']
        if len(keys) > 1:
            raise RuntimeError('Multiple keys returned')
        [obj_typename] = keys
        if self._typename is not None and obj_typename != self._typename:
            raise RuntimeError(f'Got different typename in query: {obj_typename!r} != {self._typename!r}')
        self._typename = obj_typename

        for index, json_obj in enumerate(response_data[self._typename]):
            real_index = ((page_index - 1) * self._page_size) + index
            self._fetched[real_index] = self._client.api.build_api_object(json_obj)
        return response_data

    def count(self):
        self._fetch_index(0)
        return self._total_num_objects

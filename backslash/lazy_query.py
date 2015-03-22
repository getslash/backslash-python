import collections

import requests
from sentinels import NOTHING

from ._compat import xrange, iteritems


class LazyQuery(object):

    def __init__(self, client, path=None, url=None, query_params=None, page_size=100):
        super(LazyQuery, self).__init__()
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

    def filter(self, *filter_objects, **fields):
        returned_url = self._url
        for filter_object in filter_objects:
            returned_url = filter_object.add_to_url(returned_url)
        for field_name, field_value in iteritems(fields):
            returned_url = returned_url.add_query_param(field_name, str(field_value))
        return LazyQuery(self._client, url=returned_url, page_size=self._page_size)

    def __repr__(self):
        return '<Query {0!r}>'.format(str(self._url))

    def __iter__(self):
        for i in xrange(len(self)):
            yield self._fetch_index(i)

    def __len__(self):
        if self._total_num_objects is None:
            self._fetch_page(1)
        return self._total_num_objects

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            raise NotImplementedError() # pragma: no cover
        if idx < 0:
            if idx < -len(self):
                raise IndexError()
            idx = len(self) + idx
        return self._fetch_index(idx)

    def _fetch_index(self, index):
        returned = self._fetched[index]
        if returned is NOTHING:
            page_index = (index // self._page_size) + 1
            self._fetch_page(page_index)
            returned = self._fetched[index]
            assert returned is not NOTHING
        return returned

    def _fetch_page(self, page_index):
        assert page_index != 0
        response = requests.get(self._url.add_query_param(
            'page', str(page_index)).add_query_param('page_size', str(self._page_size)))
        response.raise_for_status()
        response_data = response.json()
        if self._total_num_objects is None:
            self._total_num_objects = response_data[
                'metadata']['total_num_objects']
        for index, json_obj in enumerate(response_data['result']):
            real_index = ((page_index - 1) * self._page_size) + index
            self._fetched[real_index] = self._client.api.build_api_object(json_obj)
        return response_data

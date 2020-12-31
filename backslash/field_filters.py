from urlobject import URLObject

from typing import List, Tuple

class FieldFilter():

    def __init__(self, field_name: str) -> None:
        super().__init__()
        self.field_name = field_name
        self._filters: List[Tuple[str, str]] = []

    def add_to_url(self, url: URLObject) -> URLObject:
        for operator_name, value in self._filters:
            url = url.add_query_param(self.field_name, f'{operator_name}:{value}')
        return url

def _add_field_proxy_operator_method(operator_name: str) -> None:

    def method(self, other):
        self._filters.append((operator_name, other))  # pylint: disable=protected-access
        return self
    method_name = method.__name__ = f'__{operator_name}__'
    setattr(FieldFilter, method_name, method)

for _operator_name in ['eq', 'ne', 'lt', 'le', 'gt', 'ge']:
    _add_field_proxy_operator_method(_operator_name)


class _Fields():

    def __getattr__(self, name: str) -> FieldFilter:
        return FieldFilter(name)

FIELDS = _Fields()

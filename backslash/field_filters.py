class FieldFilter(object):

    def __init__(self, field_name, operator_name=None, value=None):
        super(FieldFilter, self).__init__()
        self.field_name = field_name
        self._filters = []

    def add_to_url(self, url):
        for operator_name, value in self._filters:
            url = url.add_query_param(self.field_name, '{0}:{1}'.format(operator_name, value))
        return url

def _add_field_proxy_operator_method(operator_name):

    def method(self, other):
        self._filters.append((operator_name, other))
        return self
    method_name = method.__name__ = '__{0}__'.format(operator_name)
    setattr(FieldFilter, method_name, method)

for _operator_name in ['eq', 'ne', 'lt', 'le', 'gt', 'ge']:
    _add_field_proxy_operator_method(_operator_name)



class _Fields(object):

    def __getattr__(self, name):
        return FieldFilter(name)

FIELDS = _Fields()

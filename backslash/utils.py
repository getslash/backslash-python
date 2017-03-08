import os
from sys import getsizeof

from requests import HTTPError


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def compute_memory_usage(obj):
    seen = set()
    stack = [obj]
    returned = 0
    while stack:
        obj = stack.pop()
        if id(obj) in seen:
            continue
        seen.add(id(obj))
        returned += getsizeof(obj)
        if isinstance(obj, dict):
            for key, value in obj.items():
                stack.append(key)
                stack.append(value)
        elif isinstance(obj, (list, tuple, set, frozenset)):
            stack.extend(obj)
    return returned


def raise_for_status(resp):
    try:
        resp.raise_for_status()
    except HTTPError as e:
        raise HTTPError(
            '{0.request.method} {0.request.url}: {0.status_code}\n\n{0.content}'.format(e.response),
            response=resp, request=resp.request)

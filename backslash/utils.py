import os
from sys import getsizeof

from typing import TypeVar

from requests import HTTPError, Response

T = TypeVar('T')


def ensure_dir(path: str) -> None:
    if not os.path.isdir(path):
        os.makedirs(path)


def compute_memory_usage(obj: T) -> int:
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


def raise_for_status(resp: Response) -> None:
    try:
        resp.raise_for_status()
    except HTTPError as e:
        raise HTTPError(
            f'{e.response.request.method} {e.response.request.url}: {e.response.status_code}\n\n{e.response.content}',
            response=resp, request=resp.request)

import os

from requests import HTTPError

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def raise_for_status(resp):
    try:
        resp.raise_for_status()
    except HTTPError as e:
        raise HTTPError(
            '{0.request.method} {0.request.url}: {0.status_code}'.format(e.response),
            response=resp, request=resp.request)

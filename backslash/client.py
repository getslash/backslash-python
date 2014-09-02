import json

import requests
from urlobject import URLObject as URL

from .api_object import APIObject


class Backslash(object):

    def __init__(self, url):
        super(Backslash, self).__init__()
        self._url = URL(url)

    def report_session_start(self):
        """Reports a new session starting

        :rtype: A session object representing the reported session
        """
        return self._call_api_single_object('report_session_start')

    def _call_api_single_object(self, params):
        returned = self._call_api(params)
        return APIObject(returned.json()['result'])

    def _call_api(self, params):
        resp = requests.post(
            self._url.add_path('api'),
            data=json.dumps(params),
            headers={'Content-type': 'application/json'},
        )
        resp.raise_for_status()
        return resp

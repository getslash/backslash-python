import json

import requests
from urlobject import URLObject as URL

from .api_object import APIObject
from ._compat import iteritems
from sentinels import NOTHING

class Backslash(object):

    def __init__(self, url):
        super(Backslash, self).__init__()
        self._url = URL(url)

    def report_session_start(self, hostname=NOTHING):
        """Reports a new session starting

        :rtype: A session object representing the reported session
        """
        return self._call_api_single_object('report_session_start', {
            'hostname': hostname,
        })

    def _call_api_single_object(self, api, params=None):
        returned = self._call_api(api, params)
        return APIObject(returned.json()['result'])

    def _call_api(self, api, params=None):
        resp = requests.post(
            self._url.add_path('api').add_path(api),
            data=self._serialize_params(params),
            headers={'Content-type': 'application/json'},
        )
        resp.raise_for_status()
        return resp

    def _serialize_params(self, params):
        if params is None:
            params = {}

        returned = {}
        for param_name, param_value in iteritems(params):
            if param_value is NOTHING:
                continue
            returned[param_name] = param_value
        return json.dumps(returned)

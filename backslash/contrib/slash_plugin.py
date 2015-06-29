import itertools
import os
import socket
import sys
import time
import webbrowser

import logbook

import requests
from urlobject import URLObject as URL

import slash
from slash.plugins import PluginInterface

from ..client import Backslash as BackslashClient
from ..utils import ensure_dir
from .utils import normalize_file_path

_SLASH_TOKEN_FILE = os.path.expanduser('~/.backslash/run_token')


class BackslashPlugin(PluginInterface):

    def __init__(self, url):
        super(BackslashPlugin, self).__init__()
        self._url = URL(url)

    def get_name(self):
        return 'backslash'

    def activate(self):
        self._runtoken = self._ensure_run_token()
        self.client = BackslashClient(self._url, self._runtoken)

    def session_start(self):
        try:
            self.session = self.client.report_session_start(
                logical_id=slash.context.session.id,
                total_num_tests=slash.context.session.get_total_num_tests(),
                hostname=socket.getfqdn(),
                metadata={
                    'slash': self._get_slash_metadata(),
                }
            )
        except Exception:
            logbook.error('Exception occurred while communicating with Backslash', exc_info=True)
            slash.plugins.manager.uninstall('backslash')

    def _get_slash_metadata(self):
        return {
            'commandline': ' '.join(sys.argv),
        }

    def test_start(self):
        self.current_test = self.session.report_test_start(
            test_logical_id=slash.context.test.__slash__.id,
            **self._get_test_info(slash.context.test)
        )

    def _get_test_info(self, test):
        return {
            'file_name': normalize_file_path(test.__slash__.file_path),
            'class_name': test.__slash__.class_name,
            'name': test.__slash__.function_name,
        }

    def test_end(self):
        self.current_test.report_end()

    def session_end(self):
        self.session.report_end()

    def error_added(self, result, error):
        kwargs = {'exception': str(error.exception),
                  'exception_type': error.exception_type.__name__,
                  'traceback': error.traceback.to_list()}
        if result is slash.session.results.global_result:
            self.session.add_error_data(**kwargs)
        self.current_test.add_error_data(**kwargs)


    #### Token Setup #########
    def _ensure_run_token(self):
        if os.path.isfile(_SLASH_TOKEN_FILE):
            with open(_SLASH_TOKEN_FILE) as f:
                token = f.read().strip()
        else:
            token = self._fetch_token()
            ensure_dir(os.path.dirname(_SLASH_TOKEN_FILE))
            with open(_SLASH_TOKEN_FILE, 'w') as f:
                f.write(token)

        return token

    def _fetch_token(self):
        opened_browser = False
        url = self._url.add_path('/runtoken/request/new')
        for retry in itertools.count():
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            if retry == 0:
                url = data['url']
            token = data.get('token')
            if token:
                return token
            if not opened_browser:
                webbrowser.open(data['complete'])
                opened_browser = True
            time.sleep(1)

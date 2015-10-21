import hashlib
import itertools
import os
import socket
import sys
import time
import webbrowser

import git
import logbook

import requests
from urlobject import URLObject as URL

import slash
from slash.plugins import PluginInterface

from sentinels import NOTHING

from ..client import Backslash as BackslashClient
from ..utils import ensure_dir
from .utils import normalize_file_path

_SLASH_TOKEN_FILE = os.path.expanduser('~/.backslash/run_token')

_logger = logbook.Logger(__name__)


class BackslashPlugin(PluginInterface):

    current_test = session = None

    def __init__(self, url):
        super(BackslashPlugin, self).__init__()
        self._url = URL(url)
        self._repo_cache = {}
        self._file_hash_cache = {}

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
            _logger.error('Exception occurred while communicating with Backslash', exc_info=True)
            slash.plugins.manager.deactivate('backslash')

    def _get_slash_metadata(self):
        return {
            'commandline': ' '.join(sys.argv),
        }

    def test_start(self):
        self.current_test = self.session.report_test_start(
            test_logical_id=slash.context.test.__slash__.id,
            **self._get_test_info(slash.context.test)
        )

    def test_skip(self, reason=None):
        self.current_test.mark_skipped(reason=reason)

    def _get_test_info(self, test):
        returned = {
            'file_name': normalize_file_path(test.__slash__.file_path),
            'class_name': test.__slash__.class_name,
            'name': test.__slash__.function_name,
        }
        self._update_scm_info(returned)
        return returned

    def _update_scm_info(self, test_info):
        test_info['file_hash'] = self._calculate_file_hash(test_info['file_name'])
        dirname = os.path.dirname(test_info['file_name'])
        repo = self._repo_cache.get(dirname, NOTHING)
        if repo is NOTHING:
            repo = self._repo_cache[dirname] = self._get_git_repo(dirname)
        if repo is None:
            return
        test_info['scm'] = 'git'
        test_info['scm_revision'] = repo.head.commit.hexsha
        test_info['scm_dirty'] = bool(repo.untracked_files or repo.index.diff(None) or repo.index.diff(repo.head.commit))

    def _calculate_file_hash(self, filename):
        returned = self._file_hash_cache.get(filename)
        if returned is None:
            try:
                with open(filename, 'rb') as f:
                    data = f.read()
                    h = hashlib.sha1()
                    h.update('blob '.encode('utf-8'))
                    h.update('{0}\0'.format(len(data)).encode('utf-8'))
                    h.update(data)
            except IOError as e:
                _logger.debug('Ignoring IOError {0!r} when calculating file hash for {1}', e, filename)
                returned = None
            else:
                returned = h.hexdigest()
            self._file_hash_cache[filename] = returned

        return returned

    def _get_git_repo(self, dirname):
        while dirname != '/':
            if os.path.isdir(os.path.join(dirname, '.git')):
                return git.Repo(dirname)
            dirname = os.path.normpath(os.path.abspath(os.path.join(dirname, '..')))
        return None

    def test_end(self):
        self.current_test.report_end()

    def session_end(self):
        self.session.report_end()

    def error_added(self, result, error):
        kwargs = {'message': str(error.exception),
                  'exception_type': error.exception_type.__name__ if error.exception_type is not None else None,
                  'traceback': error.traceback.to_list()}

        if result is slash.session.results.global_result:
            if self.session is not None:
                self.session.add_error(**kwargs)
        elif self.current_test is not None:
            if self.current_test is not None:
                self.current_test.add_error(**kwargs)

    def warning_added(self, warning):
        kwargs = {'message': warning.message, 'filename': warning.filename, 'lineno': warning.lineno}
        warning_obj = self.current_test if self.current_test is not None else self.session
        if warning_obj is not None:
            warning_obj.add_warning(**kwargs)


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
                if not webbrowser.open(data['complete']):
                    print('Could not open browser to fetch user token. Please login at', data['complete'])
                print('Waiting for Backlash token...')
                opened_browser = True
            time.sleep(1)

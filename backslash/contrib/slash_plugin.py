from __future__ import print_function

import functools
import hashlib
import itertools
import json
import os
import socket
import sys
import time
import webbrowser

import logbook
import requests

import git
import slash
from sentinels import NOTHING
from slash.plugins import PluginInterface
from urlobject import URLObject as URL

from .._compat import shellquote
from ..client import Backslash as BackslashClient
from ..client import ParamsTooLarge
from ..utils import ensure_dir
from .keepalive_thread import KeepaliveThread
from .utils import normalize_file_path

_CONFIG_FILE = os.path.expanduser('~/.backslash/config.json')

_logger = logbook.Logger(__name__)

_PWD = os.path.abspath('.')

_HAS_TEST_AVOIDED = (int(slash.__version__.split('.')[0]) >= 1)


def handle_exceptions(func):

    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception: # pylint: disable=broad-except
            exc_info = sys.exc_info()
            if not self._handle_exception(exc_info): # pylint: disable=protected-access
                raise
    return new_func


class BackslashPlugin(PluginInterface):

    current_test = session = None

    def __init__(self, url=None, keepalive_interval=None):
        super(BackslashPlugin, self).__init__()
        self._url = url
        self._repo_cache = {}
        self._file_hash_cache = {}
        self._keepalive_interval = keepalive_interval
        self._keepalive_thread = None


    def _handle_exception(self, exc_info):
        pass

    def _get_backslash_url(self):
        return self._url

    def get_name(self):
        return 'backslash'

    @handle_exceptions
    def activate(self):
        self._runtoken = self._ensure_run_token()
        self.client = BackslashClient(URL(self._get_backslash_url()), self._runtoken)

    @handle_exceptions
    def session_start(self):
        metadata = self._get_initial_session_metadata()
        try:
            self.session = self.client.report_session_start(
                logical_id=slash.context.session.id,
                total_num_tests=slash.context.session.get_total_num_tests(),
                hostname=socket.getfqdn(),
                keepalive_interval=self._keepalive_interval,
                infrastructure='slash',
                metadata=metadata,
                **self._get_extra_session_start_kwargs()
            )
        except Exception: # pylint: disable=broad-except
            raise

        if self._keepalive_interval is not None:
            self._keepalive_thread = KeepaliveThread(self.client, self.session, self._keepalive_interval)
            self._keepalive_thread.start()

    def _get_initial_session_metadata(self):
        return {'slash': self._get_slash_metadata()}

    def _get_extra_session_start_kwargs(self):
        return {}

    def _get_slash_metadata(self):
        return {
            'version': slash.__version__,
            'commandline': ' '.join(shellquote(arg) for arg in sys.argv),
        }

    @slash.plugins.register_if(_HAS_TEST_AVOIDED)
    @handle_exceptions
    def test_avoided(self, reason):
        self.test_start()
        self.test_skip(reason=reason)
        self.test_end()

    @handle_exceptions
    def test_start(self):
        self.current_test = self.session.report_test_start(
            test_logical_id=slash.context.test.__slash__.id,
            **self._get_test_info(slash.context.test)
        )

    @handle_exceptions
    def test_skip(self, reason=None):
        self.current_test.mark_skipped(reason=reason)

    def _get_test_info(self, test):
        if test.__slash__.is_interactive():
            returned = {
                'file_name': '<interactive>',
                'class_name': '<interactive>',
                'name': '<interactive>',
                'is_interactive': True
            }
        else:
            returned = {
                'file_name': normalize_file_path(test.__slash__.file_path),
                'class_name': test.__slash__.class_name,
                'name': test.__slash__.function_name,
                }
        if getattr(test.__slash__, 'variation', None) is not None:
            returned['variation'] = dict((name, str(value)) for name, value in test.__slash__.variation.items())
        self._update_scm_info(returned)
        return returned

    def _update_scm_info(self, test_info):
        try:
            test_info['file_hash'] = self._calculate_file_hash(test_info['file_name'])
            dirname = os.path.dirname(test_info['file_name'])
            repo = self._repo_cache.get(dirname, NOTHING)
            if repo is NOTHING:
                repo = self._repo_cache[dirname] = self._get_git_repo(dirname)
            if repo is None:
                return
            test_info['scm'] = 'git'
            try:
                hexsha = repo.head.commit.hexsha
            except Exception: # pylint: disable=broad-except
                _logger.debug('Unable to get commit hash', exc_info=True)
                hexsha = None
            test_info['scm_revision'] = hexsha
            test_info['scm_dirty'] = bool(repo.untracked_files or repo.index.diff(None) or repo.index.diff(repo.head.commit))
        except Exception: # pylint: disable=broad-except
            _logger.warning('Error when obtaining SCM information', exc_info=True)

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
        if not os.path.isabs(dirname):
            dirname = os.path.abspath(os.path.join(_PWD, dirname))
        while dirname != '/':
            if os.path.isdir(os.path.join(dirname, '.git')):
                return git.Repo(dirname)
            dirname = os.path.normpath(os.path.abspath(os.path.join(dirname, '..')))
        return None

    @handle_exceptions
    def test_end(self):
        details = {
            'logfile': slash.context.result.get_log_path(),
        }
        if hasattr(slash.context.result, 'details'):
            additional = slash.context.result.details.all()
        else:
            additional = slash.context.result.get_additional_details()
        details.update(additional)
        self.current_test.set_metadata_dict(details)
        self.current_test.report_end()

    @handle_exceptions
    def session_end(self):
        try:
            if self._keepalive_thread is not None:
                self._keepalive_thread.stop()
            self.session.report_end()
        except Exception:
            _logger.error('Exception ignored in session_end', exc_info=True)

    @handle_exceptions
    def error_added(self, result, error):
        kwargs = {'message': str(error.exception) if not error.message else error.message,
                  'exception_type': error.exception_type.__name__ if error.exception_type is not None else None,
                  'traceback': error.traceback.to_list()}

        for compact_variables in [False, True]:
            if compact_variables:
                for frame in kwargs['traceback']:
                    frame['globals'] = None
                    frame['locals'] = None
            try:
                if result is slash.session.results.global_result:
                    if self.session is not None:
                        self.session.add_error(**kwargs)
                elif self.current_test is not None:
                    if self.current_test is not None:
                        self.current_test.add_error(**kwargs)
            except ParamsTooLarge:
                if compact_variables:
                    raise
                # continue to try compacting
            else:
                break

    @handle_exceptions
    def warning_added(self, warning):
        kwargs = {'message': warning.message, 'filename': warning.filename, 'lineno': warning.lineno}
        warning_obj = self.current_test if self.current_test is not None else self.session
        if warning_obj is not None:
            warning_obj.add_warning(**kwargs)

    @handle_exceptions
    def exception_caught_before_debugger(self, **_):
        if self.session is not None and slash.config.root.debug.enabled:
            self.session.report_in_pdb()

    @handle_exceptions
    def exception_caught_after_debugger(self, **_):
        if self.session is not None and slash.config.root.debug.enabled:
            self.session.report_not_in_pdb()

    #### Token Setup #########
    def _ensure_run_token(self):

        tokens = self._get_existing_tokens()

        returned = tokens.get(self._get_backslash_url())
        if returned is None:
            returned = self._fetch_token()
            self._save_token(returned)

        return returned

    def _get_existing_tokens(self):
        return self._get_config().get('run_tokens', {})

    def _get_config(self):
        if not os.path.isfile(_CONFIG_FILE):
            return {}
        with open(_CONFIG_FILE) as f:
            return json.load(f)

    def _save_token(self, token):
        tmp_filename = _CONFIG_FILE + '.tmp'
        cfg = self._get_config()
        cfg.setdefault('run_tokens', {})[self._get_backslash_url()] = token

        ensure_dir(os.path.dirname(tmp_filename))

        with open(tmp_filename, 'w') as f:
            json.dump(cfg, f, indent=2)
        os.rename(tmp_filename, _CONFIG_FILE)

    def _fetch_token(self):
        opened_browser = False
        url = URL(self._get_backslash_url()).add_path('/runtoken/request/new')
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
                if not self._browse_url(data['complete']):
                    print('Could not open browser to fetch user token. Please login at', data['complete'])
                print('Waiting for Backlash token...')
                opened_browser = True
            time.sleep(1)

    def _browse_url(self, url):
        if 'linux' in sys.platform and os.environ.get('DISPLAY') is None:
            return False # can't start browser
        return webbrowser.open_new(url)

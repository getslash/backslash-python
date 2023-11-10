from __future__ import print_function

import functools
import hashlib
import itertools
import json
import os
import pkg_resources
import socket
import sys
import time
import webbrowser

import logbook
import requests
import vintage

try:
    import git
except Exception:  # pylint: disable=broad-except
    pass

import slash
from sentinels import NOTHING
from slash import config as slash_config
from slash.plugins import PluginInterface, registers_on
from slash.utils.conf_utils import Cmdline, Doc
from urlobject import URLObject as URL
from requests import HTTPError
from .._compat import shellquote
from ..client import Backslash as BackslashClient
from ..exceptions import ParamsTooLarge
from ..utils import ensure_dir
from .keepalive_thread import KeepaliveThread
from .utils import normalize_file_path, distill_slash_traceback, distill_object_attributes, add_environment_variable_metadata
from ..lazy_query import LazyQuery
from ..session import APPEND_UPCOMING_TESTS_STR
from ..__version__ import __version__ as BACKSLASH_CLIENT_VERSION

_DEFAULT_CONFIG_FILENAME = os.path.expanduser('~/.backslash/config.json')
_GET_TOKEN_TIMEOUT_SEC = 30

_logger = logbook.Logger(__name__)

_PWD = os.path.abspath('.')

_HAS_TEST_AVOIDED = (int(slash.__version__.split('.')[0]) >= 1)
_HAS_SESSION_INTERRUPT = hasattr(slash.hooks, 'session_interrupt')
_HAS_TEST_DISTRIBUTED = hasattr(slash.hooks, 'test_distributed')
_HAS_APP_QUIT = hasattr(slash.hooks, 'app_quit')

def handle_exceptions(func):

    @functools.wraps(func)
    def new_func(self, *args, **kwargs):
        try:
            with slash.exception_handling.handling_exceptions():
                return func(self, *args, **kwargs)
        except Exception: # pylint: disable=broad-except
            exc_info = sys.exc_info()
            if not self._handle_exception(exc_info) or self._propagate_exceptions: # pylint: disable=protected-access
                raise
    return new_func


class BackslashPlugin(PluginInterface):

    client = current_test = session = None

    def __init__(self, url=None, keepalive_interval=None, runtoken=None,
                 propagate_exceptions=False, config_filename=_DEFAULT_CONFIG_FILENAME):
        super().__init__()
        self._url = url
        self._repo_cache = {}
        self._config_filename = config_filename
        self._file_hash_cache = {}
        self._keepalive_interval = keepalive_interval
        self._keepalive_thread = None
        self._error_containers = {}
        self._runtoken = runtoken
        self._propagate_exceptions = propagate_exceptions
        self._started = False
        self._adding_error = False

    @property
    def rest_url(self):
        if self.client is None:
            return None
        return self.client.url.add_path('rest')

    @property
    def webapp_url(self):
        if self.client is None:
            return None
        return self.client.get_ui_url()

    @property
    def session_webapp_url(self):
        session = slash.context.session
        if session is None or self.client is None:
            return None
        return self.client.get_ui_url(f'sessions/{session.id}')

    def _handle_exception(self, exc_info):
        pass

    def _handle_keepalive_exception(self, exc_info):
        pass

    def _get_backslash_url(self):
        return self._url

    def get_name(self):
        return 'backslash'

    def get_default_config(self):
        return {
            "session_ttl_days": 0 // Doc(
                'Optional number of days after which this session will be discarded '
                'from Backslash') // Cmdline(arg='--session-ttl-days', metavar='DAYS'),


            "session_labels": [] // Doc('Specify labels to be added to the session when reported') \
                                 // Cmdline(append="--session-label", metavar="LABEL"),
            "blacklisted_warnings_category": [] // Doc(
                'Specify warnings categories which should not be reported to backslash'),
            "report_test_docstrings": False // Doc(
                'Add test docstring to backslash test metadata') // Cmdline(on="--report_test_docstrings"),
        }

    @handle_exceptions
    def activate(self):
        if self._runtoken is None:
            self._runtoken = self._ensure_run_token()
        self.client = BackslashClient(
            URL(self._get_backslash_url()),
            self._runtoken, headers=self._get_default_headers())

    def _get_default_headers(self):
        """Override this method to control the headers sent to the Backslash server
        on each reequest
        """
        return None

    def deactivate(self):
        if self._keepalive_thread is not None:
            self._keepalive_thread.stop()
        super().deactivate()

    def _notify_session_start(self):
        metadata = self._get_initial_session_metadata()
        is_parent_session = False
        parent_logical_id = child_id = None
        is_slash_support_parallel = getattr(slash_config.root, 'parallel', False)
        if is_slash_support_parallel and slash_config.root.parallel.num_workers:
            child_id = slash_config.root.parallel.worker_id
            if child_id is not None:
                parent_logical_id = getattr(slash.context.session, 'parent_session_id', None)
            else:
                is_parent_session = True

        self.session = self.client.report_session_start(
            logical_id=slash.context.session.id,
            parent_logical_id=parent_logical_id,
            is_parent_session=is_parent_session,
            child_id=child_id,
            total_num_tests=slash.context.session.get_total_num_tests(),
            hostname=socket.getfqdn(),
            keepalive_interval=self._keepalive_interval,
            infrastructure='slash',
            metadata=metadata,
            **self._get_extra_session_start_kwargs()
        )
        self._started = True
        for warning in slash.context.session.warnings:
            self.warning_added(warning)
        for label in self.current_config.session_labels:
            self.client.api.call.add_label(session_id=self.session.id, label=label)

        if self._keepalive_interval is not None:
            self._keepalive_thread = KeepaliveThread(
                self.client,
                self.session,
                self._keepalive_interval,
                error_callback=self._handle_keepalive_exception
            )
            self._keepalive_thread.start()

    @handle_exceptions
    def session_start(self):
        if self.session is None:
            self._notify_session_start()

    def _get_initial_session_metadata(self):
        returned = {
            'slash::version': slash.__version__,
            'slash::commandline': ' '.join(shellquote(arg) for arg in sys.argv),
            'backslash_client_version': BACKSLASH_CLIENT_VERSION,
            'python_version': '.'.join(map(str, sys.version_info[:3])),
            'process_id': os.getpid(),
        }

        add_environment_variable_metadata(metadata=returned)
        return returned

    def _get_extra_session_start_kwargs(self):
        returned = {}
        ttl_seconds = self.current_config.session_ttl_days * 24 * 60 * 60
        if ttl_seconds:
            returned['ttl_seconds'] = ttl_seconds
        return returned

    @slash.plugins.register_if(_HAS_TEST_AVOIDED)
    @handle_exceptions
    def test_avoided(self, reason):
        self.test_start()
        self.test_skip(reason=reason)
        self.test_end()


    @handle_exceptions
    def test_interrupt(self):
        if self.current_test is not None:
            self.current_test.report_interrupted()

    @slash.plugins.register_if(_HAS_SESSION_INTERRUPT)
    @handle_exceptions
    def session_interrupt(self):
        if self.session is not None:
            self.session.report_interrupted()

    @slash.plugins.registers_on(None)
    @handle_exceptions
    def report_planned_tests(self, tests):
        if not APPEND_UPCOMING_TESTS_STR in self.client.api.info().endpoints:
            return

        tests_metadata = []
        for test in tests:
            test_info = self._get_test_info(test)
            current = {'test_logical_id':test.__slash__.id,
                       'file_name':test_info['file_name'],
                       'name':test_info['name'],
                       'class_name':test_info['class_name']
                      }
            if 'variation' in test_info:
                current['variation'] = test_info['variation']
            tests_metadata.append(current)

        tests_count = 0
        batch_size = 100
        try:
            while tests_count < len(tests_metadata):
                self.session.report_upcoming_tests(tests_metadata[tests_count:tests_count+batch_size])
                tests_count += batch_size
        except requests.exceptions.HTTPError:
            _logger.error('Ignoring exception while reporting planned tests', exc_info=True)

    @handle_exceptions
    def test_start(self):
        kwargs = self._get_test_info(slash.context.test)
        self._update_scm_info(kwargs)
        tags = slash.context.test.__slash__.tags
        tag_dict = {tag_name: tags[tag_name] for tag_name in tags}

        if tag_dict:
            kwargs['metadata'] = {
                'slash::tags': {
                    'values': {tag_name: tag_value for tag_name, tag_value in tag_dict.items() if tag_value is not NOTHING},
                    'names': list(tag_dict),
                },
            }

        log_path = slash.context.result.get_log_path()
        if log_path:
            kwargs.setdefault('metadata', {})['local_log_path'] = os.path.abspath(log_path)

        if self.current_config.report_test_docstrings and slash.test.get_test_function().__doc__:
            kwargs.setdefault('metadata', {})['docstring'] = slash.test.get_test_function().__doc__

        self.current_test = self.session.report_test_start(
            test_logical_id=slash.context.test.__slash__.id,
            test_index=slash.context.test.__slash__.test_index1,
            **kwargs
        )
        self._error_containers[slash.context.test.__slash__.id] = self.current_test

    @slash.plugins.register_if(_HAS_TEST_DISTRIBUTED)
    @handle_exceptions #pylint: disable=unused-argument
    def test_distributed(self, test_logical_id, worker_session_id): #pylint: disable=unused-argument
        if 'report_test_distributed' in self.client.api.info().endpoints:
            self.current_test = self.session.report_test_distributed(test_logical_id)


    @handle_exceptions
    def test_skip(self, reason=None):
        self.current_test.mark_skipped(reason=reason)

    @slash.plugins.registers_on(None)
    def is_session_exist(self, session_id):
        try:
            self.client.api.get(f'/rest/sessions/{session_id}')
            return True
        except HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise

    @handle_exceptions
    @slash.plugins.registers_on(None)
    def get_tests_to_resume(self, session_id, filters_dict):
        """Queries backslash specific session's tests
        :param session_id: the wanted session
        :param filters_dict: a dictionary containing filters for backslash tests query
        :rtype: list of test objects
        """
        max_retries = 3
        for i in range(max_retries):
            try:
                default_params_dict = {x: 'true' for x in ['show_planned', 'show_skipped', 'show_unsuccessful', 'show_abandoned']}
                default_params_dict.update({'session_id': session_id, 'show_successful': 'false'})
                default_params_dict.update(filters_dict)
                return reversed(LazyQuery(self.client, '/rest/tests', query_params=default_params_dict).all())
            except HTTPError:
                if i == max_retries-1:
                    raise

    def _get_test_info(self, test):
        if test.__slash__.is_interactive() and \
           pkg_resources.parse_version(slash.__version__) < pkg_resources.parse_version('1.6.0'):
            returned = {
                'file_name': '<interactive>',
                'class_name': '<interactive>',
                'name': '<interactive>',
                'is_interactive': True
            }
        else:
            test_display_name = test.__slash__.address
            if set(test_display_name) & set('/.'):
                test_display_name = test.__slash__.function_name

            returned = {
                'file_name': normalize_file_path(test.__slash__.file_path),
                'class_name': test.__slash__.class_name,
                'name': test_display_name,
                'is_interactive': test.__slash__.is_interactive(),
                }
        variation = getattr(test.__slash__, 'variation', None)
        if variation:
            if hasattr(test.__slash__.variation, 'labels'):
                items = test.__slash__.variation.labels.items()
                returned['parameters'] = variation.values.copy()
            elif hasattr(test.__slash__.variation, 'id'):
                items = test.__slash__.variation.id.items()
                returned['parameters'] = variation.values.copy()
            else:
                items = test.__slash__.variation.items()
            returned['variation'] = dict((name, value) for name, value in items)

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
            if self.client.api.info().endpoints.report_test_start.version >= 3:
                if not repo.head.is_detached:
                    test_info['scm_local_branch'] = repo.active_branch.name
                    tracking_branch = repo.active_branch.tracking_branch()
                    if tracking_branch is not None:
                        test_info['scm_remote_branch'] = tracking_branch.name
        except Exception: # pylint: disable=broad-except
            _logger.warning('Error when obtaining SCM information', exc_info=True)

    def _calculate_file_hash(self, filename):
        returned = self._file_hash_cache.get(filename)
        if returned is None:
            try:
                with open(filename, 'rb', encoding='utf-8') as f:
                    data = f.read()
                    h = hashlib.sha1()
                    h.update('blob '.encode('utf-8'))
                    h.update(f'{len(data)}\0'.encode('utf-8'))
                    h.update(data)
            except IOError as e:
                _logger.debug(f'Ignoring IOError {e!r} when calculating file hash for {filename}')
                returned = None
            else:
                returned = h.hexdigest()
            self._file_hash_cache[filename] = returned

        return returned

    def _get_git_repo(self, dirname):
        if not os.path.isabs(dirname):
            dirname = os.path.abspath(os.path.join(_PWD, dirname))
        while dirname != os.path.normpath(os.path.abspath(os.path.sep)):
            if os.path.isdir(os.path.join(dirname, '.git')):
                return git.Repo(dirname)
            dirname = os.path.normpath(os.path.abspath(os.path.join(dirname, '..')))
        return None

    @handle_exceptions
    def test_end(self):
        if self.current_test is None:
            return

        details = {}

        if hasattr(slash.context.result, 'details'):
            additional = slash.context.result.details.all()
        else:
            additional = slash.context.result.get_additional_details()
        details.update(additional)
        self.current_test.set_metadata_dict(details)
        self.current_test.report_end()
        self.current_test = None

    @handle_exceptions
    def session_end(self):
        self._session_report_end('session_end')

    @slash.plugins.register_if(_HAS_APP_QUIT)
    @handle_exceptions  # pylint: disable=unused-argument
    def app_quit(self):
        self._session_report_end('app_quit')

    def _session_report_end(self, hook_name):
        if not self._started:
            return
        try:
            if self._keepalive_thread is not None:
                self._keepalive_thread.stop()

            kwargs = {}
            session_results = getattr(slash.session, 'results', None)
            has_fatal_errors = hasattr(session_results, 'has_fatal_errors') and session_results.has_fatal_errors()
            if self.client.api.info().endpoints.report_session_end.version >= 2:
                kwargs['has_fatal_errors'] = has_fatal_errors
            self.session.report_end(**kwargs)
            self._started = False
        except Exception:       # pylint: disable=broad-except
            _logger.error(f'Exception ignored in {hook_name}', exc_info=True)

    @handle_exceptions
    def error_added(self, result, error):
        if self._adding_error:
            return
        self._adding_error = True
        try:
            with slash.exception_handling.handling_exceptions():
                self._add_exception(result=result, exception=error, is_fatal=error.is_fatal())
        finally:
            self._adding_error = False

    @slash.plugins.register_if(hasattr(slash.hooks, 'interruption_added'))
    @handle_exceptions
    def interruption_added(self, result, exception):
        self._add_exception(result=result, exception=exception, is_interruption=True)


    def _add_exception(self, result, exception, is_interruption=False, is_fatal=False):
        has_interruptions = self.client.api.info().endpoints.add_error.version >= 4
        if is_interruption and not has_interruptions:
            _logger.debug('Server does not support recording is_interruption exceptions. Skipping reporting')
            return

        if result is slash.session.results.global_result:
            error_container = self.session
        else:
            error_container = self._error_containers.get(result.test_metadata.id, self.current_test) or self.session

        if error_container is None:
            _logger.debug('Could not determine error container to report on for {}', result)
            return

        with vintage.get_no_deprecations_context():
            exception_attrs = getattr(exception, 'exception_attributes', NOTHING)

        if exception_attrs is NOTHING and hasattr(exception, 'exc_info'):
            exception_attrs = distill_object_attributes(exception.exc_info[1])
        kwargs = {'exception_type': exception.exception_type.__name__ if exception.exception_type is not None else None,
                  'traceback': distill_slash_traceback(exception), 'exception_attrs': exception_attrs}
        if exception.message:
            message = exception.message
        elif hasattr(exception, 'exception_str'):
            message = exception.exception_str
        else:
            message = str(exception.exception)


        kwargs['message'] = message

        if has_interruptions:
            kwargs['is_interruption'] = is_interruption
        has_fatal = self.client.api.info().endpoints.add_error.version >= 5
        if has_fatal:
            kwargs['is_fatal'] = is_fatal
        for compact_variables in [False, True]:
            if compact_variables:
                for frame in kwargs['traceback']:
                    frame['globals'] = None
                    frame['locals'] = None
            try:
                error_container.add_error(**kwargs)
            except ParamsTooLarge:
                if compact_variables:
                    raise
                # continue to try compacting
            else:
                break

    @handle_exceptions
    def warning_added(self, warning):
        if any(issubclass(warning.category, b_cls) for b_cls in self.current_config.blacklisted_warnings_category):
            return
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

        if self._runtoken is None:

            tokens = self._get_existing_tokens()

            self._runtoken = tokens.get(self._get_backslash_url())
            if self._runtoken is None:
                self._runtoken = self._fetch_token()
                self._save_token(self._runtoken)

        return self._runtoken

    def _get_existing_tokens(self):
        return self._get_config().get('run_tokens', {})

    def _get_config(self):
        if not os.path.isfile(self._config_filename):
            return {}
        with open(self._config_filename, encoding='utf-8') as f:
            return json.load(f)

    def _save_token(self, token):
        tmp_filename = self._config_filename + '.tmp'
        cfg = self._get_config()
        cfg.setdefault('run_tokens', {})[self._get_backslash_url()] = token

        ensure_dir(os.path.dirname(tmp_filename))

        with open(tmp_filename, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
        os.rename(tmp_filename, self._config_filename)

    @registers_on(None)
    def fetch_token(self, username, password):
        url = URL(self._get_backslash_url())
        with requests.Session() as s:
            resp = s.get(self._get_token_request_url())
            resp.raise_for_status()
            response_url = resp.json()['url']
            request_id = response_url.split('/')[-1]
            s.post(url.add_path('login'),
                   data=json.dumps({'username': username, 'password': password}),
                   headers={'Content-type': 'application/json'})\
             .raise_for_status()

            s.post(URL(self._get_backslash_url()).add_path(f'/runtoken/request/{request_id}/complete'))\
             .raise_for_status()

            resp = s.get(response_url)
            resp.raise_for_status()
            returned = self._runtoken = resp.json()['token']
            return returned


    def _fetch_token(self):
        """Template method for the fallback behavior of fetching a runtoken from the server.
        By default this uses _fetch_token_via_browser to initiate the browser-based
        authentication.

        You can override this method to provide a custom logic for fetching your tokens
        """
        return self._fetch_token_via_browser()


    def _fetch_token_via_browser(self):
        opened_browser = False
        url = self._get_token_request_url()
        for retry in itertools.count():
            resp = requests.get(url, timeout=_GET_TOKEN_TIMEOUT_SEC)
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

    def _get_token_request_url(self):
        return URL(self._get_backslash_url()).add_path('/runtoken/request/new')

    def _browse_url(self, url):
        if 'linux' in sys.platform and os.environ.get('DISPLAY') is None:
            return False # can't start browser
        return webbrowser.open_new(url)

import pytest
from urlobject import URLObject
import slash
import slash.loader

from backslash.contrib.utils import distill_slash_traceback

# pylint: disable=redefined-outer-name


def test_importing_slash_plugin():
    from backslash.contrib import slash_plugin  # pylint: disable=unused-variable


def test_exception_distilling(traceback):
    assert isinstance(traceback, list)
    assert traceback
    for f in traceback:
        assert f['code_line']


def test_exception_distilling_surrounding_code(traceback):
    frame = traceback[-1]
    assert 'def test_failing():' in [line.strip()
                                     for line in frame['code_lines_before']]
    assert '1 / 0' in frame['code_line']
    assert frame['code_lines_before']
    assert not any('1 / 0' in l for l in frame['code_lines_before'])
    assert frame['code_lines_after']
    assert not any('1 / 0' in l for l in frame['code_lines_after'])


def test_rest_url(installed_plugin, server_url):
    assert installed_plugin.rest_url == server_url.add_path('rest')

def test_webapp_url(installed_plugin, server_url):
    expected = server_url
    if not expected.endswith('/'):
        expected += '/'
    expected += '#/'
    assert installed_plugin.webapp_url == expected

def test_session_webapp_url_no_session(installed_plugin):
    assert installed_plugin.session_webapp_url is None

def test_session_webapp_url_with_session(installed_plugin, server_url):
    with slash.Session() as s:
        url = installed_plugin.session_webapp_url
    assert url == '{}/#/sessions/{}'.format(server_url, s.id)





@pytest.fixture
def traceback(error_result):
    [e] = error_result.get_errors()
    return distill_slash_traceback(e)


@pytest.fixture
def error_result():

    def test_failing():
        1 / 0  # pylint: disable=pointless-statement

    with slash.Session() as s:
        with s.get_started_context():
            slash.runner.run_tests(
                slash.loader.Loader().get_runnables([test_failing]))
            [res] = s.results.iter_test_results()
    return res


@pytest.fixture
def installed_plugin(request, server_url):
    from backslash.contrib import slash_plugin
    plugin = slash_plugin.BackslashPlugin(url=str(server_url))

    @request.addfinalizer
    def cleanup():              # pylint: disable=unused-variable
        slash.plugins.manager.uninstall(plugin)

    slash.plugins.manager.install(plugin)
    return plugin


@pytest.fixture
def server_url():
    return URLObject('http://some.backslash.server')

from backslash import Backslash


def test_client_get_ui_url():
    assert Backslash('http://bla.com', None).get_ui_url() == 'http://bla.com/#/'
    assert Backslash('http://bla.com', None).get_ui_url('/sessions') == 'http://bla.com/#/sessions'
    assert Backslash('http://bla.com', None).get_ui_url('sessions') == 'http://bla.com/#/sessions'

from uuid import uuid4
import pytest
from backslash import Backslash
from backslash.api_object import APIObject
from backslash import test, session


def test_api_object_equality(client, data1):
    assert APIObject(client, data1) == APIObject(client, data1)
    assert not APIObject(client, data1) != APIObject(client, data1)

def test_api_object_equality_reflexive(client, data1):
    api_object = APIObject(client, data1)
    assert api_object == api_object
    assert not api_object != api_object

def test_api_object_not_equal_when_different_clients(data1):
    a = APIObject(object(), data1)
    b = APIObject(object(), data1)
    assert not a == b
    assert a != b

def test_api_object_not_equal_different_data(client, data1, data2):
    a = APIObject(client, data1)
    b = APIObject(client, data2)
    assert not a == b
    assert a != b

def test_object_api_url(client):
    data = {'api_path': '/rest/objects/1'}
    obj = APIObject(client, data)
    assert obj.api_url == 'http://127.0.0.1:12345/rest/objects/1'

def test_object_ui_url(client):
    obj = APIObject(client, {})
    with pytest.raises(NotImplementedError):
        obj.ui_url

@pytest.mark.parametrize('object_type', [test.Test, session.Session])
@pytest.mark.parametrize('use_logical', [True, False])
def test_ui_url(client, object_type, logical_id, use_logical):
    id = 1002
    data = {'id': id, 'logical_id': logical_id if use_logical else None}
    if object_type is test.Test:
        data['session_display_id'] = str(uuid4())
    obj = object_type(client, data)

    url = obj.ui_url
    display_id = logical_id if use_logical else id
    if object_type is test.Test:
        assert url == client.url + '#/sessions/{}/tests/{}'.format(data['session_display_id'], display_id)
    else:
        assert url == client.url + '#/{}s/{}'.format(object_type.__name__.lower(), display_id)


@pytest.fixture
def logical_id():
    return str(uuid4())

@pytest.fixture
def client():
    return Backslash('http://127.0.0.1:12345', runtoken=None)



@pytest.fixture
def data1():
    return {'name': 'data1'}

@pytest.fixture
def data2():
    return {'name': 'data2'}

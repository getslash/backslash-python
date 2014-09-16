import pytest
from backslash.api_object import APIObject


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

@pytest.fixture
def client():
    return object()


@pytest.fixture
def data1():
    return {'name': 'data1'}

@pytest.fixture
def data2():
    return {'name': 'data2'}

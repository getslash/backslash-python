from uuid import uuid1
import operator

from flask import Flask, jsonify
from flask_loopback import FlaskLoopback
from sentinels import NOTHING
from urlobject import URLObject as URL

import pytest
from backslash import Backslash
from backslash.lazy_query import LazyQuery
from backslash import FIELDS

# pylint: disable=redefined-outer-name

def test_all_objects(query, num_objects):
    assert [obj.id for obj in query] == list(range(num_objects))


def test_count_objects(query, num_objects):
    assert len(query) == num_objects
    assert len(query._fetched) < num_objects  # pylint: disable=protected-access


def test_getitem(query):
    assert query[20].id == 20


def test_last_item(query, num_objects, page_size):
    assert query[-1].id == num_objects - 1
    assert query._fetched[page_size] is NOTHING  # pylint: disable=protected-access


def test_slicing_not_supported(query):
    with pytest.raises(NotImplementedError):
        query[1:20]  # pylint: disable=pointless-statement


def test_querying_simple_equality(query):
    assert query._url.query == ''  # pylint: disable=protected-access
    query = query.filter(x=1)
    assert query._url.query == 'x=1'  # pylint: disable=protected-access


def test_querying_with_field_queries(query, field_value, operator_name, operator_func):
    query = query.filter(operator_func(FIELDS.field_name, field_value))
    assert query._url.query == 'field_name={0}%3A{1}'.format(  # pylint: disable=protected-access
        operator_name, field_value)

def test_querying_between(query):
    assert query.filter(1 <= FIELDS.x <= 2)._url.query == 'x=ge%3A1&x=le%3A2'  # pylint: disable=protected-access


@pytest.fixture
def query(url, page_size):
    pytest.skip('n/i')
    return LazyQuery(Backslash(url, None), path='/', page_size=page_size)


@pytest.fixture(params=['string_value', 2, 2.5])
def field_value(request):
    return request.param


@pytest.fixture(params=['eq', 'ne', 'gt', 'ge', 'lt', 'le'])
def operator_name(request):
    return request.param


@pytest.fixture
def operator_func(operator_name):
    return getattr(operator, operator_name)


@pytest.fixture
def url(request, flask_app):
    address = str(uuid1())
    returned = URL('http://{0}'.format(address))
    webapp = FlaskLoopback(flask_app)
    webapp.activate_address((address, 80))

    @request.addfinalizer
    def finalize():  # pylint: disable=unused-variable
        webapp.deactivate_address((address, 80))
    return returned


@pytest.fixture
def flask_app():

    app = Flask(__name__)
    app.config['PROPAGATE_EXCEPTIONS'] = True

    @app.route('/')
    def view_objects():  # pylint: disable=unused-variable
        return jsonify({
            'sessions': [{'id': i, 'type': 'session'}
                         for i in range(10)]})
    return app


@pytest.fixture
def page_size():
    return 10


@pytest.fixture
def num_objects():
    return 1000


def test_fake_cursor_count():
    lst = list(range(1000))
    assert FakeCursor(lst).count() == 1000
    assert FakeCursor(lst).offset(10).count() == 990
    assert FakeCursor(lst).offset(30).limit(50).count() == 50
    assert FakeCursor(lst).offset(30).limit(50000).count() == 970


class FakeCursor(object):

    def __init__(self, lst):
        super(FakeCursor, self).__init__()
        self._lst = lst
        self._iterated = False

    def __iter__(self):
        assert not self._iterated
        for item in self._lst:
            yield item

    def limit(self, limit):
        assert not self._iterated, 'Already iterated'
        return FakeCursor(self._lst[:limit])

    def offset(self, offset):
        assert not self._iterated, 'Already iterated'
        return FakeCursor(self._lst[offset:])

    def count(self):
        assert not self._iterated
        return len(self._lst)

from uuid import uuid1

from flask import Flask
from flask.ext.loopback import FlaskLoopback
from sentinels import NOTHING
from urlobject import URLObject as URL

import pytest
from backslash import Backslash
from backslash.api_object import APIObject
from backslash.lazy_query import LazyQuery
from weber_utils.pagination import paginated_view


def test_all_objects(query, num_objects):
    assert [obj.id for obj in query] == list(range(num_objects))


def test_count_objects(query, num_objects):
    assert len(query) == num_objects
    assert len(query._fetched) < num_objects

def test_getitem(query):
    assert query[20].id == 20

def test_last_item(query, num_objects, page_size):
    assert query[-1].id == num_objects - 1
    assert query._fetched[page_size] is NOTHING

def test_slicing_not_supported(query):
    with pytest.raises(NotImplementedError):
        query[1:20]


@pytest.fixture
def query(url, page_size):
    return LazyQuery(Backslash(url), '/', APIObject, page_size=page_size)


@pytest.fixture
def url(request, flask_app):
    address = str(uuid1())
    returned = URL('http://{0}'.format(address))
    webapp = FlaskLoopback(flask_app)
    webapp.activate_address((address, 80))

    @request.addfinalizer
    def finalize():
        webapp.deactivate_address((address, 80))
    return returned


@pytest.fixture
def flask_app(page_size, num_objects):

    app = Flask(__name__)
    app.config['PROPAGATE_EXCEPTIONS'] = True

    @app.route('/')
    @paginated_view(renderer=lambda obj: obj, default_page_size=page_size)
    def view_objects():
        return FakeCursor(objcount=num_objects)

    return app


@pytest.fixture
def page_size():
    return 10


@pytest.fixture
def num_objects():
    return 1000


def test_fake_cursor_count():
    assert FakeCursor(1000).count() == 1000
    assert FakeCursor(1000).offset(10).count() == 990
    assert FakeCursor(1000).offset(30).limit(50).count() == 50
    assert FakeCursor(1000).offset(30).limit(50000).count() == 970


class FakeCursor(object):

    def __init__(self, objcount=1000, offset=0, limit=None):
        super(FakeCursor, self).__init__()
        self._objcount = objcount
        self._limit = limit
        self._remaining_until_limit = limit
        self._offset = offset
        self._current = offset

    def __iter__(self):
        while self._current < self._objcount:
            if self._remaining_until_limit is not None and not self._remaining_until_limit:
                break
            yield {'id': self._current}
            if self._remaining_until_limit is not None:
                self._remaining_until_limit -= 1
            self._current += 1

    def limit(self, limit):
        return FakeCursor(objcount=self._objcount, offset=self._current, limit=limit)

    def offset(self, offset):
        assert self._current == self._offset, 'Already iterated'
        return FakeCursor(objcount=self._objcount, offset=self._offset + offset, limit=self._limit)

    def count(self):
        assert self._offset == self._current, 'Already iterated'
        returned = self._objcount - self._offset
        if self._limit is not None:
            returned = min(self._limit, returned)
        return returned

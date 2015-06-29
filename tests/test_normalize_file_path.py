import pytest
from backslash.contrib.utils import normalize_file_path


def test_normalize_file_path(file_path, expected_path):
    assert file_path != expected_path
    assert normalize_file_path(file_path) == expected_path


@pytest.fixture
def file_path(file_path_and_expected_path):
    return file_path_and_expected_path[0]

@pytest.fixture
def expected_path(file_path_and_expected_path):
    return file_path_and_expected_path[1]

@pytest.fixture
def file_path_and_expected_path(tmpdir):
    full_path = tmpdir.join('a', 'b', 'c', 'd').ensure(dir=True)
    filename = full_path.join('filename.py')
    tmpdir.join('a', 'b', '.git').ensure(dir=True)
    return filename, 'c/d/filename.py'

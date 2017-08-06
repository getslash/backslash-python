from backslash.contrib.utils import add_environment_variable_metadata

def test_environment_metadata():
    environ = {'BACKSLASH_METADATA_x': '2', 'BACKSLASH_METADATA_y': '3', 'unused': '666'}
    metadata = {'x': 'bla'}
    add_environment_variable_metadata(metadata, environ=environ.copy())
    assert metadata == {'x': '2', 'y': '3'}


def test_environment_metadata_nested():
    environ = {'BACKSLASH_METADATA_parent.child': '2', 'BACKSLASH_METADATA_parent.child2': '3', 'BACKSLASH_METADATA_x': '666'}
    metadata = {'x': 'bla'}
    add_environment_variable_metadata(metadata, environ=environ.copy())
    assert metadata == {'x': '666', 'parent': {'child': '2', 'child2': '3'}}

import os
import linecache
import ast

_SPECIAL_DIRS = ('.git', '.hg', '.svn')

_HERE = os.path.abspath('.')

def normalize_file_path(path):
    path = str(path)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(_HERE, path))
    dirname = os.path.normpath(path)
    while dirname != '/':
        for special_dir in _SPECIAL_DIRS:
            if os.path.isdir(os.path.join(dirname, special_dir)):
                return os.path.normpath(os.path.relpath(path, dirname))
        dirname = os.path.dirname(dirname)
    return path

def _is_ipython_frame(frame):
    return 'ipython-input' in frame['filename'] and frame['lineno'] == 1

def distill_slash_traceback(err, line_radius=5):
    returned = err.traceback.to_list()
    for frame in returned:
        if _is_ipython_frame(frame):
            commands = frame['locals'].get('In', {}).get('value', None)
            if not commands:
                continue
            try:
                commands = ast.literal_eval(commands)
            except SyntaxError:
                continue
            frame['code_lines_before'], frame['code_line'], frame['code_lines_after'] = _splice_lines(commands, len(commands) -1, line_radius)
            frame['lineno'] = len(commands) - 1
        else:
            lines = linecache.getlines(frame['filename'])
            lineno = frame['lineno']
            frame['code_lines_before'], _, frame['code_lines_after'] = _splice_lines(lines, lineno - 1, line_radius)
    return returned

def _splice_lines(lines, pivot, margin):
    if pivot >= len(lines):
        return ([], "<missing line>", [])
    return (lines[max(0, pivot-margin):pivot],
            lines[pivot],
            lines[pivot+1:pivot+1+margin])

_ENV_VARIABLE_METADATA_PREFIX = 'BACKSLASH_METADATA_'

def add_environment_variable_metadata(metadata, environ=None):
    if environ is None:
        environ = os.environ

    for environment_key, environment_value in environ.items():
        if environment_key.startswith(_ENV_VARIABLE_METADATA_PREFIX):
            _nested_assign(metadata, environment_key[len(_ENV_VARIABLE_METADATA_PREFIX):], environment_value)

def _nested_assign(dictionary, key, value):
    parts = key.split('.')
    for index, part in enumerate(parts):
        if index == len(parts) - 1:
            dictionary[part] = value
        else:
            dictionary = dictionary.setdefault(part, {})

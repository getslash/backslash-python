import os
import linecache

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

def distill_slash_traceback(err, line_radius=5):
    returned = err.traceback.to_list()
    for frame in returned:
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

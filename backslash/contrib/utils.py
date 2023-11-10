import ast
import linecache
import os
import types

try:
    from slash import config as slash_config
except ImportError:
    slash_config = None


_SPECIAL_DIRS = ('.git', '.hg', '.svn')

_HERE = os.path.abspath('.')

_ALLOWED_ATTRIBUTE_TYPES = [int, str, float]
_ALLOWED_ATTRIBUTE_TYPES = tuple(_ALLOWED_ATTRIBUTE_TYPES)

_FILTERED_MEMBER_TYPES = [types.MethodType, types.FunctionType, type]
_FILTERED_MEMBER_TYPES = tuple(_FILTERED_MEMBER_TYPES)

_MAX_VARIABLE_VALUE_LENGTH = 100


def normalize_file_path(path):
    path = str(path)
    if path.endswith('.pyc'):
        path = path[:-1]
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(_HERE, path))
    dirname = os.path.normpath(path)
    while dirname != os.path.normpath(os.path.abspath(os.path.sep)):
        for special_dir in _SPECIAL_DIRS:
            if os.path.isdir(os.path.join(dirname, special_dir)):
                return os.path.normpath(os.path.relpath(path, dirname))
        dirname = os.path.dirname(dirname)
    return path

def _is_ipython_frame(frame):
    return 'ipython-input' in frame['filename'] and frame['lineno'] == 1

def distill_object_attributes(obj, truncate=True):
    repr_blacklisted_types = _get_repr_blacklisted_types()

    return {attr: value
            if isinstance(value, _ALLOWED_ATTRIBUTE_TYPES) else _safe_repr(value, repr_blacklisted_types, truncate=truncate)
            for attr, value in _iter_distilled_object_attributes(obj)}

def _get_repr_blacklisted_types():
    if slash_config is None:
        return ()

    log_config = slash_config.root.log
    return getattr(log_config, 'repr_blacklisted_types', ())


def distill_slash_traceback(err, line_radius=5):
    repr_blacklisted_types = _get_repr_blacklisted_types()
    returned = _extract_frames(err.traceback, repr_blacklisted_types)
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

def _extract_frames(traceback, repr_blacklisted_types):
    returned = traceback.to_list()
    for frame, distilled_dict in zip(traceback.frames, returned):
        if 'locals' not in distilled_dict and hasattr(frame, 'python_frame'): # Slash 1.5.x deprecates the `locals` and `globals` attributes
            distilled_dict['locals'] = _capture_locals(frame.python_frame, repr_blacklisted_types)
            distilled_dict['globals'] = _capture_globals(frame.python_frame, repr_blacklisted_types)
    return returned

def _capture_locals(frame, repr_blacklisted_types):
    if frame is None:
        return None
    return {local_name: {"value": _safe_repr(local_value, repr_blacklisted_types)}
            for key, value in frame.f_locals.items()
            if "@" not in key
            for local_name, local_value in _unwrap_object_variable(key, value)}

def _unwrap_object_variable(var_name, var_value):
    yield var_name, var_value
    if var_name != 'self':
        return

    for attr, value in _iter_distilled_object_attributes(var_value):
        yield f'self.{attr}', value

def _iter_distilled_object_attributes(obj):
    try:
        obj_dict = getattr(obj, '__dict__', {})
    except Exception:       # pylint: disable=broad-except
        obj_dict = {}

    for attr in obj_dict:
        if attr.startswith('__') and attr.endswith('__'):
            continue
        try:
            value = getattr(obj, attr)
        except Exception:   # pylint: disable=broad-except
            continue
        if isinstance(value, _FILTERED_MEMBER_TYPES):
            continue
        yield attr, value

def _capture_globals(frame, repr_blacklisted_types):
    if frame is None:
        return None
    used_globals = set(frame.f_code.co_names)
    return dict((global_name, {"value": _safe_repr(value, repr_blacklisted_types)})
                for global_name, value in frame.f_globals.items()
                if global_name in used_globals and _is_global_included(value))

def _is_global_included(global_variable):
    if isinstance(global_variable, (types.FunctionType, types.MethodType, types.ModuleType, type)):
        return False
    return True

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

def _safe_repr(value, repr_blacklisted_types, truncate=True):
    if isinstance(value, repr_blacklisted_types):
        returned = f"<{type(value).__name__!r} object {id(value):x}>"

    try:
        returned = repr(value)
    except Exception:  # pylint: disable=broad-except
        return f"[Unprintable {type(value).__name__!r} object]"

    if truncate and len(returned) > _MAX_VARIABLE_VALUE_LENGTH:
        returned = returned[:_MAX_VARIABLE_VALUE_LENGTH - 3] + '...'
    return returned

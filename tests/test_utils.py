from backslash.utils import compute_memory_usage

def test_getsizeof():
    large_object = {'x': (1, 2, 3), 'y': [1, 2, 3, 4, 5], 'd': {'key': 'hey', 'key2': {}, 'key3': ["", {}, ()]}}
    assert compute_memory_usage(large_object) > large_object.__sizeof__()

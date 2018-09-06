import sys
import pytest
import numpy as np
import itertools
try:
    from next.apps.Butler import Memory
except:
    sys.path.append('..')
    sys.path.append('../..')
    sys.path.append('../../..')
    sys.path.append('../../../..')
    from Butler import Memory


def test_ensure_connection():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem._ensure_connection()


@pytest.mark.parametrize("value", [
    'bar', 1, 2, {'dict': True}, ('tuple', True),
    [1, 2, 3], ['1', '2']
])
def test_set_and_get(value):
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem.set('foo-gs', value)
    assert mem.get('foo-gs') == value


def test_exists():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem.set('foo-exist', 'bar')
    assert mem.exists('foo-exist')


def test_append():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem.set('foo-append2', [1, 2, 3])
    assert mem.append('foo-append2', [4])
    assert mem.get('foo-append2') == [1, 2, 3, 4]

def test_append_no_initial():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    for i in itertools.count(start=0, step=1):
        key = 'foo-append' + str(hash(i))
        if mem.exists(key):
            continue
        mem.append(key, [4])
        assert mem.get(key) == [4]
        break


def test_get_ndarray():
    x = np.linspace(0, 1)
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem.set('x', x)
    y = mem.get('x')
    assert np.allclose(x, y)


def test_increment():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    mem.set('foo-incr', 0)
    assert mem.increment('foo-incr') == 1
    assert mem.increment('foo-incr', value=2) == 3

def test_set_many():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    values = {'a': 1, 'b': 2}
    mem.set_many(values)

    out = {k: mem.get(k) for k in values}
    assert out == values

def test_get_many():
    mem = Memory(exp_uid=hash(1), uid_prefix='abc')
    values = {'a': 1, 'b': 2}
    for k, v in values.items():
        mem.set(k, v)
    keys = list(values.keys())
    out = mem.get_many(keys)
    assert values == out

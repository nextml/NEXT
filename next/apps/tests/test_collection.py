import pytest

from next.database_client.DatabaseAPI import to_db_fmt, from_db_fmt, DatabaseAPI, DatabaseException
from next.apps.Butler import Collection

# IMPORTANT NOTE: only uses the `test_data` database; it gets cleared after each test session
MONGO_HOST, MONGO_PORT = 'localhost', 27017
MONGO_DB = 'test_data'

# === fixtures ===
@pytest.fixture(scope='module')
def db():
    db = DatabaseAPI(MONGO_HOST, MONGO_PORT, MONGO_DB)
    yield db
    db.client.drop_database(MONGO_DB)
    db.client.close()

# === tests ===
def test_uid_prefix(db):
    B = 'test_uid_prefix'
    c = Collection(B, '', 'exp_uid', db)
    c.set('obj', value={'f': 2})
    assert db.get_doc(B, 'obj')['f'] == 2

    c = Collection(B, 'asdf:', 'exp_uid', db)
    c.set('obj', value={'f': 2})
    assert db.get_doc(B, 'asdf:obj')['f'] == 2

    c = Collection(B, 'asdf_{exp_uid}:', 'exp_uid', db)
    c.set('obj', value={'f': 2})
    assert db.get_doc(B, 'asdf_exp_uid:obj')['f'] == 2

def test_set(db):
    B = 'test_set'
    c = Collection(B, '', '', db)
    c.set('c', value={'x': 2})
    c.set('c', 'y', 3)
    assert db.get(B, 'c', 'x') == 2
    assert db.get(B, 'c', 'y') == 3

def test_get(db):
    B = 'test_get'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'd', {'x': 2, 'z': 4})
    assert c.get('d')['x'] == 2 and c.get('d')['z'] == 4
    assert c.get('d', 'x') == 2 and c.get('d', 'z') == 4

def test_get_and_delete(db):
    B = 'test_get_and_delete'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'asdf', {'a': 3})
    assert c.get_and_delete('asdf', 'a') == 3
    assert db.get(B, 'asdf', 'a') is None

def test_exists(db):
    B = 'test_exists'
    c = Collection(B, '', '', db)
    assert not c.exists('f')
    db.set_doc(B, 'f', {})
    assert c.exists('f')

def test_increment(db):
    B = 'test_increment'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'f', {'a': 0})
    c.increment('f', 'a')
    assert db.get(B, 'f', 'a') == 1
    c.increment('f', 'a', value=2)
    assert db.get(B, 'f', 'a') == 3

def test_increment_many(db):
    B = 'test_increment_many'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'f', {'a': 0, 'b': 1})
    c.increment_many('f', {'a': -1, 'b': 2})
    assert db.get(B, 'f', 'a') == -1 and db.get(B, 'f', 'b') == 3

def test_append(db):
    B = 'test_append'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'f', {'a': [1,3]})
    c.append('f', 'a', 10)
    assert db.get(B, 'f', 'a') == [1,3,10]

def test_pop(db):
    B = 'test_pop'
    c = Collection(B, '', '', db)
    db.set_doc(B, 'f', {'a': [1,3,10]})
    # pop one by one and check that everything is as expected
    assert c.pop('f', 'a') == 10
    assert db.get(B, 'f', 'a') == [1,3]
    assert c.pop('f', 'a') == 3
    assert db.get(B, 'f', 'a') == [1]
    assert c.pop('f', 'a') == 1
    assert db.get(B, 'f', 'a') == []
    with pytest.raises(IndexError):
        c.pop('f', 'a')

    # TODO: test pop from head

def test_timing(db):
    B = 'test_timing'
    c = Collection(B, '', '', db)
    assert c.get_durations == 0 and c.set_durations == 0
    c.set('f', 'a', 'aafhjk')
    assert c.set_durations > 0 and c.get_durations == 0
    c.get('f', 'a')
    assert c.set_durations > 0 and c.get_durations > 0

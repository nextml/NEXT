import pytest

import pymongo

from next.database_client.DatabaseAPI import to_db_fmt, from_db_fmt, DatabaseAPI, DatabaseException

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

# === basic tests ===
def test_connect(db):
    assert db.is_connected()

def test_reconnection(db):
    db.connect_mongo(MONGO_HOST, MONGO_PORT)
    assert db.is_connected()

# === test db functions ===
def test__bucket(db):
    assert db._bucket('foo') == db.client[MONGO_DB]['foo']

def test_exists(db):
    B = 'test_exists'

    doc_uid = db._bucket(B).insert_one({'a_key': 2}).inserted_id

    assert db.exists(B, doc_uid, 'a_key')
    assert not db.exists(B, doc_uid, 'a_nonexistent_key')
    assert not db.exists(B, 'ashkjfdbkjfns', 'a_key')

def test_get(db):
    B = 'test_get'

    doc_uid = db._bucket(B).insert_one({'a_key': 2, 'another_key': [1.0, 'f']}).inserted_id

    assert db.get(B, doc_uid, 'a_key') == 2
    assert db.get(B, doc_uid, 'another_key') == [1.0, 'f']
    assert not db.get(B, doc_uid, 'a_nonexistant_key')

def test_get_many(db):
    B = 'test_get_many'
    doc = {'a_key': 2, 'another_key': [1.0, 'f'], 'third_key': 'baz'}

    doc_uid = db._bucket(B).insert_one(doc).inserted_id

    assert db.get_many(B, doc_uid, ['another_key']) \
        == {'another_key': [1.0, 'f']}
    assert db.get_many(B, doc_uid, ['another_key', 'third_key']) \
        == {'another_key': [1.0, 'f'], 'third_key': 'baz'}

    assert db.get_many(B, doc_uid, ['totally_nonexistent_key', 'another_key']) \
        == {'totally_nonexistent_key': None, 'another_key': [1.0, 'f']}

def test_get_and_delete(db):
    B = 'test_get_and_delete'
    doc = {'a': 2, 'b': [1.0, 'f'], 'c': 'baz'}

    doc_uid = db._bucket(B).insert_one(doc).inserted_id

    assert db.exists(B, doc_uid, 'b')
    assert db.get_and_delete(B, doc_uid, 'b') == [1.0, 'f']
    assert not db.exists(B, doc_uid, 'b')

def test_increment(db):
    B = 'test_increment'
    
    doc_uid = db._bucket(B).insert_one({'a': 2}).inserted_id

    assert db.increment(B, doc_uid, 'a') == 3
    assert db.get(B, doc_uid, 'a') == 3
    assert db.increment(B, doc_uid, 'a', -2) == 1
    assert db.get(B, doc_uid, 'a') == 1

def test_increment_many(db):
    B = 'test_increment_many'
    doc = {'a': 0, 'b': 0, 'c': 0}
    
    doc_uid = db._bucket(B).insert_one(doc).inserted_id

    assert db.increment_many(B, doc_uid, {'a': 1, 'b': 5, 'c': -7}) \
                    == {'a': 1, 'b': 5, 'c': -7}
    assert db.get_many(B, doc_uid, ['a', 'b', 'c']) \
                    == {'a': 1, 'b': 5, 'c': -7}

def test_pop_list(db):
    B = 'test_pop_list'
    doc = {'a': range(0, 10+1)}

    doc_uid = db._bucket(B).insert_one(doc).inserted_id

    assert db.pop_list(B, doc_uid, 'a', -1) == 10
    assert db.get(B, doc_uid, 'a') == range(0, 9+1)

    assert db.pop_list(B, doc_uid, 'a', 0) == 0
    assert db.get(B, doc_uid, 'a') == range(1, 9+1)

    # popping from an empty list should raise an exception
    db.set(B, doc_uid, 'a', [])
    with pytest.raises(DatabaseException):
        db.pop_list(B, doc_uid, 'a', 0)

def test_append_list(db):
    B = 'test_append_list'

    doc_uid = db._bucket(B).insert_one({'a': [1, 2, 3, 4]}).inserted_id

    assert db.append_list(B, doc_uid, 'a', 10) == [1, 2, 3, 4, 10]
    assert db.get(B, doc_uid, 'a') == [1, 2, 3, 4, 10]

def test_set(db):
    B = 'test_set_list'

    doc_uid = db._bucket(B).insert_one({}).inserted_id

    assert db.get(B, doc_uid, 'a') == None
    db.set(B, doc_uid, 'a', [1,2,3,4])
    assert db.get(B, doc_uid, 'a') == [1,2,3,4]
    # alias of db.set()
    db.set_list(B, doc_uid, 'a', [5,6,7,8])
    assert db.get(B, doc_uid, 'a') == [5,6,7,8]

def test_set_many(db):
    B = 'test_set_many'

    doc_uid = db._bucket(B).insert_one({'a': 3, 'x': 'bar'}).inserted_id

    assert db.get(B, doc_uid, 'a') == 3
    assert db.get(B, doc_uid, 'x') == 'bar'

    # db.set_many() takes a dict and sets multiple keys
    db.set_many(B, doc_uid, {'a': 4, 'b': 'foo'})
    assert db.get_doc(B, doc_uid) == {'_id': str(doc_uid), 'a': 4, 'b': 'foo', 'x': 'bar'}

def test_set_doc(db):
    B = 'test_set_doc'

    doc_uid = db._bucket(B).insert_one({}).inserted_id

    # replace an existing document
    assert db.get_doc(B, doc_uid) == {'_id': str(doc_uid)}
    db.set_doc(B, doc_uid, {'a': 5, 'b': 'foo'})
    assert db.get_doc(B, doc_uid) == {'_id': str(doc_uid),
        'a': 5, 'b': 'foo'}

    # add a new document with _id='asdf'
    db.set_doc(B, 'asdf', {'a': 3, 'b': 'baz'})
    assert db.get_doc(B, 'asdf') == {'_id': 'asdf',
        'a': 3, 'b': 'baz'}

def test_get_doc(db):
    B = 'test_get_doc'

    doc_uid = db._bucket(B).insert_one({'a': 3}).inserted_id

    assert db.get_doc(B, doc_uid) == {'_id': str(doc_uid), 'a': 3}

def test_get_docs_with_filter(db):
    B = 'test_get_doc'

    db._bucket(B).insert_many([
        {'a': 3, 'b': 2},
        {'a': 5, 'b': 2},
        {'a': 1, 'b': 3}])

    retrieved_docs = db.get_docs_with_filter(B, {'b': 2})
    # remove `_id`s for asserts
    retrieved_docs = [{k: v for k, v in r.items() if k != '_id'}
        for r in retrieved_docs]
    assert {'a': 3, 'b': 2} in retrieved_docs
    assert {'a': 5, 'b': 2} in retrieved_docs
    assert {'a': 1, 'b': 3} not in retrieved_docs

def test_delete(db):
    B = 'test_delete'

    doc_uid = db._bucket(B).insert_one({'a': 3}).inserted_id

    assert db.get(B, doc_uid, 'a') == 3
    db.delete(B, doc_uid, 'a')
    assert db.get(B, doc_uid, 'a') == None

def test_indexes(db):
    B = 'test_indexes'

    # index a key, 'a'. we should see that index when listing indexes.
    db.ensure_index(B, {'a': pymongo.ASCENDING})
    indexes = list(db._bucket(B).list_indexes())
    assert any([i.get('key').get('a') is not None for i in indexes])

    # drop indexes. we shouldn't see an index on 'a' now.
    db.drop_all_indexes(B)
    indexes = list(db._bucket(B).list_indexes())
    assert all([i.get('key').get('a') is None for i in indexes])

def test_delete_docs_with_filter(db):
    B = 'test_delete_docs_with_filter'

    db._bucket(B).insert_many([{'a': 2}, {'a': 2, 'b': 3}, {'a': 6}])

    db.delete_docs_with_filter(B, {'a': 2})

    docs = [{k:v for k, v in d.items() if k != '_id'} for d in db._bucket(B).find()]
    assert docs == [{'a': 6}]

# === test utils ===
def test_to_db_fmt():
    import cPickle
    import numpy as np
    from bson.binary import Binary

    # standard types should be passed through
    assert to_db_fmt(1) == 1
    assert to_db_fmt(4.2) == 4.2
    assert to_db_fmt('foobarbaz') == 'foobarbaz'
    assert to_db_fmt(1+2j) == 1+2j

    # lists and dicts should be recursively formatted
    assert to_db_fmt([1, 1+2j, 'foo', [1,2.3]]) == [1, 1+2j, 'foo', [1,2.3]]
    assert to_db_fmt({'a': 1, 'b': ['foo', 2]}) == {'a': 1, 'b': ['foo', 2]}

    # numpy arrays should be converted to lists
    assert to_db_fmt(np.array([1,2,3])) == [1,2,3]

    # objects should be pickled
    x = object()
    assert to_db_fmt(x) == Binary(cPickle.dumps(x, protocol=2))

def test_from_db_fmt():
    import cPickle
    import numpy as np

    def does_invert(x):
        return from_db_fmt(to_db_fmt(x)) == x

    # standard types should invert to the original
    assert does_invert(1)
    assert does_invert(4.2)
    assert does_invert('foobarbaz')
    assert does_invert(1+2j)

    # lists and dicts should invert 
    assert does_invert([1, 1+2j, 'foo', [1,2.3]])
    assert does_invert({'a': 1, 'b': ['foo', 2]})

    # numpy arrays invert to lists
    assert from_db_fmt(to_db_fmt(np.array([1,2,3]))) == [1,2,3]
